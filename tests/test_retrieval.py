
from __future__ import annotations
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
def test_basic_query_path():
    from agent.chat_sql import answer_question

    ans = answer_question("Count companies")
    assert isinstance(ans, str)
    assert len(ans) > 0
