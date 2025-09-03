from __future__ import annotations
"""Small validation helpers for environment and DB connectivity."""
import logging
from typing import Sequence
from sqlalchemy import text
from .database import get_engine
from .config import settings

logger = logging.getLogger(__name__)


def validate_env(required_vars: Sequence[str]) -> None:
    """Raise if any of the required environment variables are missing."""
    missing = []
    for var in required_vars:
        if not getattr(settings, var.lower(), None):
            missing.append(var)
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def validate_db_schema() -> None:
    """Attempt a trivial connection to Postgres to fail fast on misconfig."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # basic smoke check
            conn.execute(text("SELECT 1"))
        logger.info("Database schema validation successful")
    except Exception as e:
        logger.error(f"Database schema validation failed: {e}")
        raise


