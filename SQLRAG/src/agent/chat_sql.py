from __future__ import annotations
"""SQL-first chat pipeline with performance optimizations.

This module wires together:
- Prompt to generate a single SQL query from a user question
- Execution of that SQL against Postgres with connection pooling
- Rewriting the result into a natural language answer with inline sources


Only the Pydantic response schema class lives in models.py; everything else
here is function-based per project requirements.
"""
import logging
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .prompts import sql_query_prompt, generation_answer_prompt
from core.utils import sanitize_sql
from core.config import settings, validate_config
from core.monitoring import monitor_query_performance
from core.models import SQLQuery

logger = logging.getLogger(__name__)

# Global instances (initialized lazily)
_db: SQLDatabase = None
_llm: ChatOpenAI = None
_structured_llm = None


def get_database() -> SQLDatabase:
    """Get database instance with lazy initialization."""
    global _db
    if _db is None:
        _db = SQLDatabase.from_uri(settings.database_url)
        logger.info("Database connection initialized")
    return _db


def get_llm() -> ChatOpenAI:
    """Get LLM instance with lazy initialization."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.openai_model, 
            temperature=0,
            api_key=settings.openai_api_key
        )
        logger.info(f"LLM initialized with model: {settings.openai_model}")
    return _llm


def get_structured_llm():
    """Get structured LLM instance with lazy initialization."""
    global _structured_llm
    if _structured_llm is None:
        llm = get_llm()
        _structured_llm = llm.with_structured_output(SQLQuery)
    return _structured_llm


def get_database_schema() -> str:
    """Get database schema."""
    db = get_database()
    return db.get_table_info()


def is_broad_question(question: str) -> bool:
    """Check if the question is too broad and might return too much data."""
    broad_keywords = [
        "all companies", "every company", "list all", "show all", "all data",
        "everything", "complete list", "full list", "entire", "all records",
        "all financial", "all metrics", "all revenue", "all profit"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in broad_keywords)


@monitor_query_performance()
def generate_sql(question: str, session_id: str) -> str:
    """Generate SQL query with performance monitoring and automatic LIMIT for broad questions."""
    schema = get_database_schema()
    structured_llm = get_structured_llm()
    
    # Modify question if it's too broad
    modified_question = question
    if is_broad_question(question):
        modified_question = f"{question} (Please limit results to top 10 most relevant entries for a summary)"
        logger.info("Question appears broad, adding LIMIT constraint")
    
    result = (sql_query_prompt | structured_llm).invoke(
        {
            "schema": schema,
            "question": modified_question,
            "chat_history": [],
        }
    )
    sql_text = sanitize_sql(result.sql)
    
    # Add LIMIT if not present and question is broad
    if is_broad_question(question) and "LIMIT" not in sql_text.upper():
        sql_text = f"{sql_text.rstrip(';')} LIMIT 10;"
        logger.info("Added LIMIT 10 to prevent large result set")
    
    logger.debug("Generated SQL: %s", sql_text)
    return sql_text


@monitor_query_performance()
def run_sql(sql: str):
    """Execute SQL query with performance monitoring."""
    if not sql or not sql.strip():
        logger.warning("Empty SQL provided to run_sql")
        return ""
    
    try:
        db = get_database()
        result = db.run(sql)
        logger.debug("SQL executed successfully")
        return result
    except Exception as exc:
        logger.error("SQL execution failed: %s", exc)
        raise


def get_rephrase_chain():
    """Get rephrase answer chain with lazy initialization."""
    llm = get_llm()
    return generation_answer_prompt | llm | StrOutputParser()


def truncate_large_result(result: str, max_rows: int = 20) -> str:
    """Truncate large SQL results to prevent token limit issues."""
    if not result or not result.strip():
        return result
    
    lines = result.strip().split('\n')
    if len(lines) <= max_rows:
        return result
    
    # Keep header and first few rows, add truncation notice
    truncated_lines = lines[:max_rows]
    truncated_lines.append(f"\n... (showing first {max_rows} rows out of {len(lines)} total rows)")
    truncated_lines.append("Note: This is a summary due to large dataset size. Please be more specific for detailed information.")
    
    return '\n'.join(truncated_lines)


@monitor_query_performance()
def answer_question(question: str, session_id: str = "default") -> str:
    """High-level pipeline: question → SQL → execution → answer string with size management."""
    validate_config()
    
    generated_sql = generate_sql(question, session_id)
    rephrase_chain = get_rephrase_chain()
    
    # Execute SQL and check result size
    sql_result = run_sql(generated_sql)
    truncated_result = truncate_large_result(sql_result)
    
    # If result was truncated, modify the question context
    modified_question = question
    if truncated_result != sql_result:
        modified_question = f"{question} (Note: This is a summary of the data - please be more specific for detailed information)"
        logger.info("Result was large, providing summary instead of full data")
    
    chain = (
        RunnablePassthrough.assign(query=lambda _: generated_sql).assign(
            result=lambda d: truncated_result
        )
        | rephrase_chain
    )
    return chain.invoke({"question": modified_question, "chat_history": []})


