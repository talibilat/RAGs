import argparse
from pathlib import Path

from src.config.settings import settings
from src.parsing.parse import AzureParser, build_session_factory_from_url, parse_next_pending_document


def run_step02(
    parsed_dir: Path,
    database_url: str = settings.postgres_dsn,
    pages: str | None = None,
    fail_fast: bool = False,
):
    parsed_dir.mkdir(parents=True, exist_ok=True)
    parser = AzureParser.from_settings()
    session_factory = build_session_factory_from_url(database_url)

    print(f"Extracting text to {parsed_dir}...")
    count = 0
    failed = 0
    while True:
        try:
            result = parse_next_pending_document(
                parser=parser,
                parsed_dir=parsed_dir,
                session_factory=session_factory,
                tenant_id="qasper_eval",
                pages=pages,
            )
        except Exception as exc:
            failed += 1
            print(f"Parse failed; marked document failed and continuing: {exc}")
            if fail_fast:
                raise
            continue

        if result is None:
            break
        
        count += 1
        print(
            f"Parsed document_id={result.document_id} version_id={result.version_id} "
            f"markdown={result.markdown_path}"
        )
    
    print(f"Finished. Parsed {count} documents. Failed {failed} documents.")


def main():
    parser = argparse.ArgumentParser(description="QASPER Step 02: Extract text from PDFs.")
    parser.add_argument("--parsed-dir", type=Path, default=Path("data/processed/pdf_text"))
    parser.add_argument("--pages", type=str, help="Page range to parse (e.g. '1-5')")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on the first parse failure.")
    args = parser.parse_args()

    run_step02(parsed_dir=args.parsed_dir, pages=args.pages, fail_fast=args.fail_fast)


if __name__ == "__main__":
    main()
