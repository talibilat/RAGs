import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import settings
from src.ingestion.ingest import build_session_factory
from src.ledger.models import Document, DocumentStatus, DocumentVersion


SessionFactory = Callable[[], Session]


class Parser(Protocol):
    def parse(self, path: Path) -> "ParseResult":
        ...


@dataclass(frozen=True)
class ParseResult:
    markdown: str
    raw_response: dict[str, Any] | None = None
    structural_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedDocumentResult:
    document_id: int
    version_id: int
    markdown_path: Path
    raw_response_path: Path | None


class AzureParser:
    def __init__(
        self,
        endpoint: str,
        key: str,
        *,
        max_attempts: int = 3,
        retry_wait_seconds: float = 2.0,
    ) -> None:
        if not endpoint:
            raise ValueError("Azure Document Intelligence endpoint is required")
        if not key:
            raise ValueError("Azure Document Intelligence key is required")
        self.endpoint = endpoint
        self.key = key
        self.max_attempts = max_attempts
        self.retry_wait_seconds = retry_wait_seconds

    @classmethod
    def from_settings(cls) -> "AzureParser":
        return cls(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT or "",
            key=settings.AZURE_DOCUMENT_INTELLIGENCE_KEY or "",
        )

    def parse(self, path: Path, pages: str | None = None) -> ParseResult:
        return self._retry(lambda: self._parse_once(path, pages=pages))

    def _parse_once(self, path: Path, pages: str | None = None) -> ParseResult:
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.ai.documentintelligence.models import DocumentContentFormat as ContentFormat
            from azure.core.credentials import AzureKeyCredential
        except ImportError as exc:
            raise RuntimeError(
                "Azure parsing requires azure-ai-documentintelligence. "
                "Install requirements.txt before using AzureParser."
            ) from exc

        client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key),
        )
        with Path(path).open("rb") as document:
            poller = client.begin_analyze_document(
                "prebuilt-layout",
                body=document,
                output_content_format=ContentFormat.MARKDOWN,
                pages=pages,
            )
            result = poller.result()

        markdown = getattr(result, "content", None)
        if not markdown:
            raise RuntimeError("Azure Document Intelligence returned no markdown content")

        raw_response = _to_jsonable(result)
        return ParseResult(
            markdown=markdown,
            raw_response=raw_response,
            structural_metadata=_extract_structural_metadata(raw_response),
        )

    def _retry(self, operation: Callable[[], ParseResult]) -> ParseResult:
        try:
            from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
        except ImportError:
            return self._retry_without_tenacity(operation)

        @retry(
            retry=retry_if_exception(_is_transient_error),
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=self.retry_wait_seconds, min=1, max=30),
            reraise=True,
        )
        def run() -> ParseResult:
            return operation()

        return run()

    def _retry_without_tenacity(self, operation: Callable[[], ParseResult]) -> ParseResult:
        last_error: BaseException | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()
            except BaseException as exc:
                last_error = exc
                if attempt == self.max_attempts or not _is_transient_error(exc):
                    raise
                time.sleep(self.retry_wait_seconds * attempt)
        raise RuntimeError("retry loop exited unexpectedly") from last_error


def parse_next_pending_document(
    parser: Parser,
    parsed_dir: Path | str,
    session_factory: SessionFactory,
    tenant_id: str | None = None,
    pages: str | None = None,
) -> ParsedDocumentResult | None:
    parsed_dir = Path(parsed_dir)
    selected = _claim_next_pending_version(session_factory, tenant_id=tenant_id)
    if selected is None:
        return None

    document_id, version_id, storage_path = selected
    markdown_path = parsed_dir / f"{document_id}.md"
    raw_response_path: Path | None = None

    print(f"Parsing document_id={document_id} version_id={version_id} path={storage_path}...")
    try:
        parse_result = parser.parse(storage_path, pages=pages)
        parsed_dir.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(parse_result.markdown, encoding="utf-8")

        if parse_result.raw_response is not None:
            raw_response_path = parsed_dir / f"{document_id}.json"
            raw_response_path.write_text(
                json.dumps(parse_result.raw_response, indent=2, sort_keys=True),
                encoding="utf-8",
            )

        _set_version_status(session_factory, version_id, DocumentStatus.PARSED)
        return ParsedDocumentResult(
            document_id=document_id,
            version_id=version_id,
            markdown_path=markdown_path,
            raw_response_path=raw_response_path,
        )
    except BaseException:
        _set_version_status(session_factory, version_id, DocumentStatus.FAILED)
        raise


def _claim_next_pending_version(
    session_factory: SessionFactory,
    tenant_id: str | None = None,
) -> tuple[int, int, Path] | None:
    with session_factory() as session:
        query = (
            select(DocumentVersion)
            .join(Document)
            .where(DocumentVersion.status == DocumentStatus.PENDING)
        )
        if tenant_id:
            query = query.where(Document.tenant_id == tenant_id)
            
        version = session.scalar(
            query.order_by(DocumentVersion.id).limit(1)
        )
        if version is None:
            return None

        document_id = version.document_id
        version_id = version.id
        storage_path = Path(version.document.storage_path)
        version.status = DocumentStatus.PARSING
        session.commit()
        return document_id, version_id, storage_path


def _set_version_status(
    session_factory: SessionFactory,
    version_id: int,
    status: DocumentStatus,
) -> None:
    with session_factory() as session:
        version = session.get(DocumentVersion, version_id)
        if version is None:
            raise RuntimeError(f"DocumentVersion {version_id} disappeared during parsing")
        version.status = status
        session.commit()


def _is_transient_error(exc: BaseException) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {408, 409, 429, 500, 502, 503, 504}:
        return True
    return isinstance(exc, (ConnectionError, TimeoutError))


def _to_jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, dict):
        return value
    try:
        return dict(value)
    except (TypeError, ValueError):
        return {"repr": repr(value)}


def _extract_structural_metadata(raw_response: dict[str, Any]) -> dict[str, Any]:
    pages = raw_response.get("pages") or []
    tables = raw_response.get("tables") or []
    return {
        "pages": [
            {
                "page_number": page.get("pageNumber") or page.get("page_number"),
                "width": page.get("width"),
                "height": page.get("height"),
                "unit": page.get("unit"),
            }
            for page in pages
            if isinstance(page, dict)
        ],
        "tables": [
            {
                "row_count": table.get("rowCount") or table.get("row_count"),
                "column_count": table.get("columnCount") or table.get("column_count"),
                "bounding_regions": table.get("boundingRegions")
                or table.get("bounding_regions")
                or [],
            }
            for table in tables
            if isinstance(table, dict)
        ],
    }


def build_session_factory_from_url(database_url: str) -> sessionmaker[Session]:
    return build_session_factory(database_url)


def main() -> None:
    cli = argparse.ArgumentParser(
        description="Parse one pending ledger document with Azure Document Intelligence."
    )
    cli.add_argument("--parsed-dir", type=Path, default=Path("data/parsed"))
    cli.add_argument("--database-url", default=settings.postgres_dsn)
    args = cli.parse_args()

    result = parse_next_pending_document(
        AzureParser.from_settings(),
        args.parsed_dir,
        build_session_factory_from_url(args.database_url),
    )
    if result is None:
        print("no pending documents")
        return
    print(
        f"document_id={result.document_id} version_id={result.version_id} "
        f"markdown={result.markdown_path}"
    )


if __name__ == "__main__":
    main()
