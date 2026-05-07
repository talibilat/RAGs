from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy.orm import Session

from src.ingestion.ingest import (
    IngestDirectoryResult,
    apply_schema,
    build_session_factory,
    ingest_directory,
)


def seed_documents(
    *,
    source_dir: Path,
    storage_dir: Path,
    tenant_id: str,
    count: int,
    session_factory,
) -> IngestDirectoryResult:
    source_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, count + 1):
        path = source_dir / f"synthetic-{index:04d}.pdf"
        if not path.exists():
            path.write_bytes(_synthetic_pdf_bytes(index))

    return ingest_directory(source_dir, storage_dir, tenant_id, session_factory)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic PDFs into the ledger.")
    parser.add_argument("--source-dir", type=Path, default=Path("data/incoming/step08_1000"))
    parser.add_argument("--storage-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--tenant-id", default="tenant-step08")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument(
        "--database-url",
        default="postgresql://postgres:postgres@localhost:5432/rag_ledger",
    )
    parser.add_argument("--apply-schema", action="store_true")
    args = parser.parse_args()

    if args.apply_schema:
        apply_schema(args.database_url)
    session_factory = build_session_factory(args.database_url)
    result = seed_documents(
        source_dir=args.source_dir,
        storage_dir=args.storage_dir,
        tenant_id=args.tenant_id,
        count=args.count,
        session_factory=session_factory,
    )
    print(
        f"seen={result.total_seen} created={result.created} "
        f"skipped_duplicates={result.skipped_duplicates}"
    )


def _synthetic_pdf_bytes(index: int) -> bytes:
    body = (
        "%PDF-1.7\n"
        f"1 0 obj << /Type /Catalog /SyntheticDocument {index} >> endobj\n"
        f"% synthetic scalable-rag evidence document {index}\n"
        "%%EOF\n"
    )
    return body.encode("utf-8")


if __name__ == "__main__":
    main()
