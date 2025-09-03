from __future__ import annotations
"""ETL utilities for loading JSON 9fin financials into PostgreSQL.

This module provides a simple Extract-Transform-Load pipeline:
- create_schema: ensures DB extensions and tables exist
- upsert_company_financials: stores the raw JSON documents per company
- normalize_metrics: flattens time-series metrics into a fact table
- normalize_cap_table: flattens capital structure into a fact table

Only SQLAlchemy models are classes (see models.py). All logic here is
function-based for clarity and testability.
"""
import os
import json
import datetime
from typing import Dict, Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .models import (
    Base,
    CompanyFinancials,
    FinancialMetricsNormalized,
    CapTableNormalized,
    DATABASE_URL,
)


def get_engine():
    """Create a SQLAlchemy engine using environment-based URL."""
    return create_engine(DATABASE_URL, echo=False, future=True)


def create_schema(engine):
    """Create required DB extension and all ORM tables if missing."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    Base.metadata.create_all(engine)


def load_json(path: str) -> Dict[str, Any]:
    """Read a JSON file from disk and return the parsed object."""
    with open(path, "r") as f:
        return json.load(f)


def upsert_company_financials(session, company_record: Dict[str, Any]):
    """Insert or update a `company_financials` JSON document.

    If the company already exists, mutable fields are overwritten so the
    table always reflects the latest JSON snapshot.
    """
    obj = CompanyFinancials(
        company_id=company_record["company_id"],
        company=company_record["company"],
        currency=company_record["currency"],
        periods=company_record["periods"],
        key_financials=company_record["key_financials"],
        cash_flow_and_leverage=company_record["cash_flow_and_leverage"],
        cap_table=company_record["cap_table"],
    )
    existing = session.get(CompanyFinancials, company_record["company_id"]) 
    if existing:
        for attr in [
            "company",
            "currency",
            "periods",
            "key_financials",
            "cash_flow_and_leverage",
            "cap_table",
        ]:
            setattr(existing, attr, getattr(obj, attr))
    else:
        session.add(obj)


def normalize_metrics(session, company_record: Dict[str, Any]):
    """Flatten `key_financials` and `cash_flow_and_leverage` into facts.

    Each metric value across periods is stored as a single row with
    explicit unit, period_date, and period_type.
    """
    periods = company_record["periods"]
    indexed_periods = [(i + 1, p["date"], p["period"]) for i, p in enumerate(periods)]

    def insert_rows(section_key: str, category: str):
        src = company_record[section_key]
        url = src.get("url")
        if not url:
            raise AssertionError("source_url is required")
        for row in src["rows"]:
            metric = row["metric"]
            unit = row["unit"]
            values = row["values"]
            for idx, value in enumerate(values, start=1):
                period_date, period_type = indexed_periods[idx - 1][1], indexed_periods[idx - 1][2]
                fact = FinancialMetricsNormalized(
                    company_id=company_record["company_id"],
                    metric_name=metric,
                    category=category,
                    unit=unit,
                    period_date=period_date,
                    period_type=period_type,
                    value=value,
                    source_url=url,
                )
                session.merge(fact)

    insert_rows("key_financials", "key_financials")
    insert_rows("cash_flow_and_leverage", "cash_flow_and_leverage")


def normalize_cap_table(session, company_record: Dict[str, Any]):
    """Flatten `cap_table` into a normalized fact table."""
    cap = company_record["cap_table"]
    url = cap.get("url")
    if not url:
        raise AssertionError("source_url is required")
    as_of = cap.get("as_of")
    for row in cap["rows"]:
        maturity = row.get("maturity")
        maturity_date = None
        if maturity and maturity not in ("Various", "N/A"):
            try:
                maturity_date = datetime.datetime.strptime(maturity, "%b-%Y").date()
            except Exception:
                maturity_date = None
        fact = CapTableNormalized(
            company_id=company_record["company_id"],
            instrument_name=row.get("name"),
            note=row.get("note"),
            security=row.get("security"),
            maturity_date=maturity_date,
            rate=row.get("rate"),
            amount_usdm=row.get("amount_usdm"),
            x_ebitda=row.get("x_ebitda"),
            percent_cap=row.get("percent_cap"),
            is_subtotal=bool(row.get("subtotal", False)),
            as_of_date=as_of,
            source_url=url,
        )
        session.add(fact)


def main():
    """Entry point for running the ETL from the command line."""
    engine = get_engine()
    create_schema(engine)
    Session = sessionmaker(bind=engine, future=True)
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "financial_data.json")
    data = load_json(data_path)

    with Session() as session:
        for company_record in data["company_financials"]:
            upsert_company_financials(session, company_record)
            normalize_metrics(session, company_record)
            normalize_cap_table(session, company_record)
        session.commit()


if __name__ == "__main__":
    main()

 
