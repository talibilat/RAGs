from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.ingestion.ingest import ingest_directory, ingest_file
from src.ledger.models import Base, Document, DocumentStatus, DocumentVersion


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ledger.db'}", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


def write_pdf(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.7\n" + content)
    return path


def test_ingest_file_copies_raw_file_and_creates_pending_ledger_entry(
    tmp_path, session_factory
):
    source = write_pdf(tmp_path / "source" / "alpha.pdf", b"alpha")
    storage_dir = tmp_path / "data" / "raw"

    result = ingest_file(
        source_path=source,
        storage_dir=storage_dir,
        tenant_id="tenant-a",
        session_factory=session_factory,
    )

    assert result.created is True
    assert result.document_id is not None
    assert result.sha256_hash
    assert result.storage_path.exists()
    assert result.storage_path.read_bytes() == source.read_bytes()

    with session_factory() as session:
        document = session.scalar(select(Document))
        version = session.scalar(select(DocumentVersion))

    assert document.filename == "alpha.pdf"
    assert document.tenant_id == "tenant-a"
    assert document.sha256_hash == result.sha256_hash
    assert version.document_id == document.id
    assert version.version_hash == result.sha256_hash
    assert version.status == DocumentStatus.PENDING


def test_ingest_file_skips_duplicate_content_for_same_tenant(tmp_path, session_factory):
    first = write_pdf(tmp_path / "first.pdf", b"same-content")
    second = write_pdf(tmp_path / "second.pdf", b"same-content")
    storage_dir = tmp_path / "data" / "raw"

    first_result = ingest_file(first, storage_dir, "tenant-a", session_factory)
    second_result = ingest_file(second, storage_dir, "tenant-a", session_factory)

    assert first_result.created is True
    assert second_result.created is False
    assert second_result.document_id == first_result.document_id

    with session_factory() as session:
        documents = session.scalars(select(Document)).all()
        versions = session.scalars(select(DocumentVersion)).all()

    assert len(documents) == 1
    assert len(versions) == 1


def test_ingest_file_allows_same_content_for_different_tenants(tmp_path, session_factory):
    first = write_pdf(tmp_path / "tenant-a.pdf", b"shared-content")
    second = write_pdf(tmp_path / "tenant-b.pdf", b"shared-content")
    storage_dir = tmp_path / "data" / "raw"

    first_result = ingest_file(first, storage_dir, "tenant-a", session_factory)
    second_result = ingest_file(second, storage_dir, "tenant-b", session_factory)

    assert first_result.created is True
    assert second_result.created is True
    assert second_result.document_id != first_result.document_id

    with session_factory() as session:
        documents = session.scalars(select(Document).order_by(Document.tenant_id)).all()

    assert [document.tenant_id for document in documents] == ["tenant-a", "tenant-b"]
    assert documents[0].sha256_hash == documents[1].sha256_hash


def test_ingest_directory_registers_only_new_pdfs(tmp_path, session_factory):
    source_dir = tmp_path / "incoming"
    write_pdf(source_dir / "one.pdf", b"one")
    write_pdf(source_dir / "two.pdf", b"two")
    write_pdf(source_dir / "notes.txt", b"not-a-pdf")
    storage_dir = tmp_path / "data" / "raw"

    first_run = ingest_directory(source_dir, storage_dir, "tenant-a", session_factory)
    second_run = ingest_directory(source_dir, storage_dir, "tenant-a", session_factory)

    assert first_run.total_seen == 2
    assert first_run.created == 2
    assert first_run.skipped_duplicates == 0
    assert second_run.total_seen == 2
    assert second_run.created == 0
    assert second_run.skipped_duplicates == 2

    with session_factory() as session:
        documents = session.scalars(select(Document)).all()

    assert len(documents) == 2
