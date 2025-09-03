from __future__ import annotations
"""SQL-first chat pipeline.

This module wires together:
- Prompt to generate a single SQL query from a user question
- Execution of that SQL against Postgres
- Rewriting the result into a natural language answer with inline sources

Only the Pydantic response schema class lives in models.py; everything else
here is function-based per project requirements.
"""
import os
import logging
import dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .prompts import sql_query_prompt, generation_answer_prompt
from .utils import sanitize_sql
from .validation import validate_env
from .models import SQLQuery


dotenv.load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# Reduce noisy transport logs (e.g., HTTP Request: POST ...)
for noisy_logger in ("httpx", "httpcore"):
    nl = logging.getLogger(noisy_logger)
    nl.setLevel(logging.WARNING)
    nl.propagate = False
logger = logging.getLogger(__name__)

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOSTNAME = os.getenv("DATABASE_HOSTNAME")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
DATABASE_URL = f"postgresql+psycopg2://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"



if os.environ.get("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_TRACING"] = "true"


db = SQLDatabase.from_uri(DATABASE_URL)
schema = db.get_table_info()
llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
structured_llm = llm.with_structured_output(SQLQuery)


def generate_sql(question: str, session_id: str) -> str:
    result = (sql_query_prompt | structured_llm).invoke(
        {
            "schema": schema,
            "question": question,
            "chat_history": [],
        }
    )
    sql_text = sanitize_sql(result.sql)
    logger.debug("Generated SQL: %s", sql_text)
    return sql_text


rephrase_answer = generation_answer_prompt | llm | StrOutputParser()


def run_sql(sql: str):
    if not sql or not sql.strip():
        logger.warning("Empty SQL provided to run_sql")
        return ""
    try:
        result = db.run(sql)
        logger.debug("SQL executed successfully")
        return result
    except Exception as exc:
        logger.error("SQL execution failed: %s", exc)
        raise


def answer_question(question: str, session_id: str = "default") -> str:
    """High-level pipeline: question → SQL → execution → answer string."""
    validate_env([
        "DATABASE_USERNAME",
        "DATABASE_PASSWORD",
        "DATABASE_HOSTNAME",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
    ])
    generated_sql = generate_sql(question, session_id)
    chain = (
        RunnablePassthrough.assign(query=lambda _: generated_sql).assign(
            result=lambda d: run_sql(d["query"])
        )
        | rephrase_answer
    )
    return chain.invoke({"question": question, "chat_history": []})


