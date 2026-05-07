import argparse
import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.ledger.models import Base, Document, DocumentStatus, DocumentVersion


SessionFactory = Callable[[], Session]


@dataclass(frozen=True)
class IngestFileResult:
    source_path: Path
    storage_path: Path
    sha256_hash: str
    document_id: int
    created: bool


@dataclass(frozen=True)
class IngestDirectoryResult:
    total_seen: int
    created: int
    skipped_duplicates: int
    results: tuple[IngestFileResult, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest_file(
    source_path: Path | str,
    storage_dir: Path | str,
    tenant_id: str,
    session_factory: SessionFactory,
) -> IngestFileResult:
    source_path = Path(source_path)
    storage_dir = Path(storage_dir)

    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    content_hash = sha256_file(source_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / tenant_id / f"{content_hash}{source_path.suffix.lower()}"

    with session_factory() as session:
        existing = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.sha256_hash == content_hash,
            )
        )
        if existing is not None:
            return IngestFileResult(
                source_path=source_path,
                storage_path=Path(existing.storage_path),
                sha256_hash=content_hash,
                document_id=existing.id,
                created=False,
            )

        storage_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, storage_path)

        document = Document(
            filename=source_path.name,
            sha256_hash=content_hash,
            tenant_id=tenant_id,
            storage_path=str(storage_path),
        )
        document.versions.append(
            DocumentVersion(version_hash=content_hash, status=DocumentStatus.PENDING)
        )
        session.add(document)
        session.commit()

        return IngestFileResult(
            source_path=source_path,
            storage_path=storage_path,
            sha256_hash=content_hash,
            document_id=document.id,
            created=True,
        )


def iter_ingestable_files(source_dir: Path) -> Iterable[Path]:
    return sorted(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")


def ingest_directory(
    source_dir: Path | str,
    storage_dir: Path | str,
    tenant_id: str,
    session_factory: SessionFactory,
) -> IngestDirectoryResult:
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise NotADirectoryError(source_dir)

    results = tuple(
        ingest_file(path, storage_dir, tenant_id, session_factory)
        for path in iter_ingestable_files(source_dir)
    )
    created = sum(1 for result in results if result.created)
    skipped = sum(1 for result in results if not result.created)
    return IngestDirectoryResult(
        total_seen=len(results),
        created=created,
        skipped_duplicates=skipped,
        results=results,
    )


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, future=True)
    return sessionmaker(bind=engine, future=True)


def apply_schema(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Register local PDFs in the ingestion ledger.")
    parser.add_argument("source", type=Path, help="PDF file or directory containing PDFs")
    parser.add_argument("--storage-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument(
        "--database-url",
        default="postgresql://postgres:postgres@localhost:5432/rag_ledger",
    )
    parser.add_argument("--apply-schema", action="store_true")
    args = parser.parse_args()

    if args.apply_schema:
        apply_schema(args.database_url)

    session_factory = build_session_factory(args.database_url)
    if args.source.is_dir():
        result = ingest_directory(args.source, args.storage_dir, args.tenant_id, session_factory)
        print(
            f"seen={result.total_seen} created={result.created} "
            f"skipped_duplicates={result.skipped_duplicates}"
        )
    else:
        result = ingest_file(args.source, args.storage_dir, args.tenant_id, session_factory)
        print(
            f"file={result.source_path} created={result.created} "
            f"document_id={result.document_id} sha256={result.sha256_hash}"
        )


if __name__ == "__main__":
    main()
