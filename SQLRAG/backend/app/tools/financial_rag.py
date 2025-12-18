"""Financial RAG with production-ready error handling and SQL safety."""
from __future__ import annotations
import logging
import re
from typing import Optional

from langchain_openai import AzureChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# --- Prompts ---
sql_query_prompt = PromptTemplate.from_template(
    """Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
    
    Use the following format:
    
    Question: "Question here"
    SQLQuery: "SQL Query to run"
    SQLResult: "Result of the SQLQuery"
    Answer: "Final answer here"
    
    Only use the following tables:
    {table_info}
    
    IMPORTANT SECURITY RULES:
    - Only generate SELECT queries, never INSERT, UPDATE, DELETE, DROP, ALTER, or any DDL/DML statements
    - Do not use any subqueries that modify data
    - Limit results to 100 rows maximum
    
    Question: {input}
    """
)

generation_answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question.
    
    Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    Answer: """
)

# Global instances (initialized lazily)
_db: SQLDatabase = None
_llm: AzureChatOpenAI = None


# Dangerous SQL patterns to block
DANGEROUS_SQL_PATTERNS = [
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE)\b',
    r'\b(EXEC|EXECUTE)\b',
    r'--',  # SQL comments that could hide malicious code
    r';.*\b(DROP|DELETE|UPDATE|INSERT)\b',  # Multi-statement attacks
]


def is_safe_sql(sql: str) -> bool:
    """Check if SQL query is safe to execute (read-only)."""
    sql_upper = sql.upper()
    for pattern in DANGEROUS_SQL_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            logger.warning(f"Blocked potentially dangerous SQL pattern: {pattern}")
            return False
    return True


def get_database() -> SQLDatabase:
    """Get database instance with lazy initialization."""
    global _db
    if _db is None:
        try:
            _db = SQLDatabase.from_uri(settings.database_url)
            logger.info("Financial RAG Database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    return _db


def get_llm() -> AzureChatOpenAI:
    """Get LLM instance with lazy initialization."""
    global _llm
    if _llm is None:
        try:
            _llm = AzureChatOpenAI(
                azure_deployment=settings.azure_openai_deployment,
                openai_api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                temperature=0,
                request_timeout=settings.query_timeout,
            )
            logger.info("Financial RAG LLM initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    return _llm


def generate_sql(question: str) -> str:
    """Generate SQL query with error handling."""
    logger.info("Generating SQL query", extra={"extra_data": {"question_length": len(question)}})
    
    try:
        llm = get_llm()
        db = get_database()
        
        from langchain.chains import create_sql_query_chain
        chain = create_sql_query_chain(llm, db)
        sql = chain.invoke({"question": question})
        
        logger.debug(f"Generated SQL: {sql[:200]}...")  # Truncate for logging
        return sql
        
    except Exception as e:
        logger.error(f"SQL generation failed: {e}", exc_info=True)
        raise


def run_sql(sql: str) -> str:
    """Execute SQL query with safety checks and error handling."""
    logger.info("Executing SQL query")
    
    # Safety check
    if not is_safe_sql(sql):
        error_msg = "Query blocked: Contains potentially dangerous SQL operations"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    
    try:
        db = get_database()
        
        # Add LIMIT if not present for safety
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper and "SELECT" in sql_upper:
            sql = sql.rstrip(";") + " LIMIT 100;"
            logger.debug("Added LIMIT 100 to query for safety")
        
        result = db.run(sql)
        logger.debug(f"SQL execution successful, result length: {len(str(result))}")
        return result
        
    except Exception as e:
        logger.error(f"SQL execution failed: {e}", exc_info=True)
        return f"Error: Database query failed - {str(e)}"


def answer_financial_question(question: str) -> str:
    """
    High-level pipeline: question → SQL → execution → answer.
    Production-ready with comprehensive error handling.
    """
    logger.info("Processing financial question", extra={"extra_data": {"question": question[:100]}})
    
    try:
        # Generate SQL
        generated_sql = generate_sql(question)
        # Sanitize markdown code blocks
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        
        logger.info(f"Generated SQL for question: {generated_sql[:200]}")
        
        # Execute SQL
        sql_result = run_sql(generated_sql)
        
        # Check for errors in result
        if sql_result.startswith("Error:"):
            return sql_result
        
        # Generate answer
        llm = get_llm()
        chain = generation_answer_prompt | llm | StrOutputParser()
        
        answer = chain.invoke({
            "question": question,
            "query": generated_sql,
            "result": sql_result
        })
        
        logger.info("Financial question answered successfully")
        return answer
        
    except Exception as e:
        logger.error(f"Failed to answer financial question: {e}", exc_info=True)
        return f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your query."

