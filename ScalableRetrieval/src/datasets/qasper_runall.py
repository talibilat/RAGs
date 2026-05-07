import argparse
import json
from pathlib import Path
from src.datasets.qasper_step01_ingest import run_step01
from src.datasets.qasper_step02_parse import run_step02
from src.datasets.qasper_step03_index import run_step03
from src.datasets.qasper_step04_eval import run_step04
from src.datasets.qasper_step05_report import run_step05

def main():
    parser = argparse.ArgumentParser(description="Run the full QASPER Retrieval Evaluation Pipeline.")
    parser.add_argument("--limit", type=int, help="Limit number of documents to ingest.")
    parser.add_argument(
        "--all-documents",
        action="store_true",
        help="Ingest every document listed in data/manifest.json.",
    )
    parser.add_argument(
        "--pages",
        type=str,
        default=None,
        help="Optional page range to parse, for example '1-10'. Defaults to all pages.",
    )
    parser.add_argument("--strategy", default="section_aware", help="Chunking strategy (default: section_aware).")
    args = parser.parse_args()

    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed" / "pdf_text"
    eval_gold = data_dir / "eval" / "qasper_qa_gold.jsonl"
    report_json = Path("reports/qasper_metrics.json")
    report_md = Path("reports/qasper_evaluation.md")
    limit = _resolve_limit(data_dir / "manifest.json", args.limit, args.all_documents)

    print("=== Step 01: Ingestion ===")
    run_step01(manifest_path=data_dir / "manifest.json", storage_dir=raw_dir, limit=limit)

    print("\n=== Step 02: Extraction (Parsing) ===")
    run_step02(parsed_dir=processed_dir, pages=args.pages)

    print("\n=== Step 03: Indexing ===")
    run_step03(parsed_dir=processed_dir, strategy=args.strategy)

    print("\n=== Step 04: Evaluation ===")
    run_step04(gold_path=eval_gold, report_path=report_json)

    print("\n=== Step 05: Reporting ===")
    run_step05(metrics_json=report_json, output_md=report_md)

    print("\n=== Pipeline Complete! ===")
    print(f"Final Report: {report_md}")


def _resolve_limit(manifest_path: Path, limit: int | None, all_documents: bool) -> int | None:
    if limit is not None and all_documents:
        raise SystemExit("--limit and --all-documents cannot be used together.")
    if not all_documents:
        return limit

    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)
    return len(manifest.get("documents", []))

if __name__ == "__main__":
    main()
