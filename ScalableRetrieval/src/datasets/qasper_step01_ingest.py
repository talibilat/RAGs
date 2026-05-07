import argparse
import json
import random
from pathlib import Path

from src.config.settings import settings
from src.ingestion.ingest import build_session_factory, ingest_file


def run_step01(
    manifest_path: Path,
    storage_dir: Path,
    database_url: str = settings.postgres_dsn,
    limit: int | None = None,
):
    if limit is None:
        limit = settings.QASPER_EVAL_LIMIT
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    documents = manifest.get("documents", [])
    if not documents:
        print("No documents found in manifest.")
        return

    # Randomly sample documents using a fixed seed for reproducibility
    random.seed(42)
    sampled_docs = random.sample(documents, min(len(documents), limit))

    session_factory = build_session_factory(database_url)

    print(f"Ingesting {len(sampled_docs)} sampled documents...")
    for doc in sampled_docs:
        pdf_path = Path(doc["pdf_path"])
        # If path is relative, make it relative to manifest location or root
        if not pdf_path.is_absolute():
             # For this script, we assume paths are relative to the project root
             pdf_path = Path(".") / pdf_path

        result = ingest_file(
            source_path=pdf_path,
            storage_dir=storage_dir,
            tenant_id="qasper_eval",
            session_factory=session_factory,
        )
        print(f"Document {doc['doc_id']}: created={result.created} id={result.document_id}")


def main():
    parser = argparse.ArgumentParser(description="QASPER Step 01: Ingest sampled PDFs.")
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.json"))
    parser.add_argument("--storage-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    run_step01(manifest_path=args.manifest, storage_dir=args.storage_dir)


if __name__ == "__main__":
    main()
