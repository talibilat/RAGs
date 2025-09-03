from __future__ import annotations
"""Small validation helpers for environment and DB connectivity."""
import os
from typing import Sequence
from sqlalchemy import create_engine, text


def validate_env(required_vars: Sequence[str]) -> None:
    """Raise if any of the required environment variables are missing."""
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def validate_db_schema() -> None:
    """Attempt a trivial connection to Postgres to fail fast on misconfig."""
    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOSTNAME")
    port = os.getenv("DATABASE_PORT")
    name = os.getenv("DATABASE_NAME")
    url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{name}"
    engine = create_engine(url, echo=False, future=True)
    with engine.connect() as conn:
        # basic smoke check
        conn.execute(text("SELECT 1"))


