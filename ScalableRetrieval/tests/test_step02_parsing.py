import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.ingestion.ingest import ingest_file
from src.ledger.models import Base, DocumentStatus, DocumentVersion
from src.parsing.parse import ParseResult, parse_next_pending_document


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ledger.db'}", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


@dataclass
class RecordingParser:
    result: ParseResult
    received_path: Path | None = None

    def parse(self, path: Path, pages: str | None = None) -> ParseResult:
        self.received_path = path
        return self.result


class FailingParser:
    def parse(self, path: Path, pages: str | None = None) -> ParseResult:
        raise RuntimeError(f"cannot parse {path.name}")


def write_pdf(path: Path, content: bytes = b"source") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.7\n" + content)
    return path


def pending_version(session_factory) -> DocumentVersion:
    with session_factory() as session:
        return session.scalar(select(DocumentVersion))


def test_parse_next_pending_document_writes_markdown_and_marks_version_parsed(
    tmp_path, session_factory
):
    source = write_pdf(tmp_path / "incoming" / "financials.pdf")
    ingest_result = ingest_file(source, tmp_path / "data" / "raw", "tenant-a", session_factory)
    parser = RecordingParser(
        ParseResult(
            markdown="# Financials\n\n| Name | Revenue |\n| - | -: |\n| Alpha | 10 |\n",
            raw_response={"model_id": "prebuilt-layout", "pages": [{"page_number": 1}]},
        )
    )

    result = parse_next_pending_document(parser, tmp_path / "data" / "parsed", session_factory)

    assert result is not None
    assert result.document_id == ingest_result.document_id
    assert result.markdown_path == tmp_path / "data" / "parsed" / f"{ingest_result.document_id}.md"
    assert result.markdown_path.read_text() == parser.result.markdown
    assert result.raw_response_path is not None
    assert json.loads(result.raw_response_path.read_text()) == parser.result.raw_response
    assert parser.received_path == ingest_result.storage_path
    assert pending_version(session_factory).status == DocumentStatus.PARSED


def test_parse_next_pending_document_returns_none_when_no_pending_versions(
    tmp_path, session_factory
):
    result = parse_next_pending_document(
        RecordingParser(ParseResult(markdown="unused")), tmp_path / "parsed", session_factory
    )

    assert result is None


def test_parse_next_pending_document_marks_version_failed_when_parser_raises(
    tmp_path, session_factory
):
    source = write_pdf(tmp_path / "incoming" / "broken.pdf")
    ingest_file(source, tmp_path / "data" / "raw", "tenant-a", session_factory)

    with pytest.raises(RuntimeError, match="cannot parse"):
        parse_next_pending_document(FailingParser(), tmp_path / "data" / "parsed", session_factory)

    assert pending_version(session_factory).status == DocumentStatus.FAILED
    assert not (tmp_path / "data" / "parsed").exists()
