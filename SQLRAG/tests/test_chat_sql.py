from __future__ import annotations
"""Basic smoke tests for the SQL chat pipeline.

These tests are designed to run against a local Postgres (docker-compose)
and require environment variables for DB and OpenAI to be set. To make the
suite CI-friendly, we only check that functions return strings and that the
SQL generator emits non-empty text for a trivial schema.
"""
import os
import pytest


@pytest.mark.skipif(
    not (
        os.getenv("DATABASE_USERNAME")
        and os.getenv("DATABASE_PASSWORD")
        and os.getenv("DATABASE_HOSTNAME")
        and os.getenv("DATABASE_PORT")
        and os.getenv("DATABASE_NAME")
        and os.getenv("OPENAI_API_KEY")
        and os.getenv("OPENAI_MODEL")
    ),
    reason="DB/OpenAI env not configured",
)
def test_answer_question_smoke():
    from agent.chat_sql import answer_question

    out = answer_question("How many companies are there?", session_id="test")
    assert isinstance(out, str)
    assert len(out) > 0


