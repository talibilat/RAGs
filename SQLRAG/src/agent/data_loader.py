from __future__ import annotations
"""ETL utilities for loading JSON 9fin financials into PostgreSQL with performance optimizations.

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
import logging
from typing import Dict, Any
from sqlalchemy import text

from core.models import Base, CompanyFinancials, FinancialMetricsNormalized, CapTableNormalized
from core.database import get_engine, get_db_session, optimize_database_connections
from core.config import settings

logger = logging.getLogger(__name__)


def create_schema():
    """Create required DB extension and all ORM tables if missing."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    Base.metadata.create_all(engine)
    logger.info("Database schema created/verified")


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
    logger.info("Starting ETL process")
    
    # Create schema and optimize database
    create_schema()
    optimize_database_connections()
    
    # Load data
    data_path = settings.data_path
    if not os.path.isabs(data_path):
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), data_path)
    
    data = load_json(data_path)
    logger.info(f"Loaded {len(data['company_financials'])} company records")

    with get_db_session() as session:
        for i, company_record in enumerate(data["company_financials"], 1):
            try:
                upsert_company_financials(session, company_record)
                normalize_metrics(session, company_record)
                normalize_cap_table(session, company_record)
                
                if i % 10 == 0:  # Log progress every 10 records
                    logger.info(f"Processed {i}/{len(data['company_financials'])} companies")
                    
            except Exception as e:
                logger.error(f"Error processing company {company_record.get('company_id', 'unknown')}: {e}")
                raise
    
    logger.info("ETL process completed successfully")


if __name__ == "__main__":
    main()

 
