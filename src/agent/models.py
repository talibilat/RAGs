
from __future__ import annotations
"""SQLAlchemy ORM models and lightweight Pydantic schema.

Per project requirements, classes are only used here for DB models and
the typed response container used by the LLM structured output.
"""
import os
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    Boolean,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field


DATABASE_HOSTNAME = os.getenv("DATABASE_HOSTNAME", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "9fin")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "password")

DATABASE_URL = (
    f"postgresql+psycopg2://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"
)

Base = declarative_base()


class CompanyFinancials(Base):
    """Raw JSON document for each company; serves as the source of truth."""
    __tablename__ = "company_financials"

    company_id = Column(Integer, primary_key=True)
    company = Column(String(255), nullable=False)
    currency = Column(String(50), nullable=False)
    periods = Column(JSON, nullable=False)
    key_financials = Column(JSON, nullable=False)
    cash_flow_and_leverage = Column(JSON, nullable=False)
    cap_table = Column(JSON, nullable=False)


class FinancialMetricsNormalized(Base):
    """Flattened time-series metrics across periods and categories."""
    __tablename__ = "financial_metrics_normalized"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, nullable=False)
    metric_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    unit = Column(String(50), nullable=False)
    period_date = Column(Date, nullable=False)
    period_type = Column(String(20), nullable=False)
    value = Column(Numeric(15, 2))
    source_url = Column(String(500), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "metric_name",
            "period_date",
            "period_type",
            "category",
            name="uq_metrics_unique_fact",
        ),
    )


class CapTableNormalized(Base):
    """Normalized capital structure rows, one row per instrument/subtotal."""
    __tablename__ = "cap_table_normalized"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, nullable=False)
    instrument_name = Column(String(500), nullable=False)
    note = Column(String(10))
    security = Column(String(50))
    maturity_date = Column(Date)
    rate = Column(String(50))
    amount_usdm = Column(Numeric(12, 2))
    x_ebitda = Column(Numeric(8, 2))
    percent_cap = Column(Numeric(8, 2))
    is_subtotal = Column(Boolean, default=False)
    as_of_date = Column(Date, nullable=False)
    source_url = Column(String(500), nullable=False)


class SQLQuery(BaseModel):
    sql: str = Field(description="PostgreSQL query only. No markdown fences, no commentary.")
