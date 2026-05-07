import argparse
import json
from pathlib import Path


def run_step05(
    metrics_json: Path,
    output_md: Path,
):
    with metrics_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    agg = data["aggregate_metrics"]
    results = data["individual_results"]

    markdown = []
    markdown.append("# QASPER Retrieval Evaluation Report")
    markdown.append("")
    markdown.append("## Aggregate Metrics")
    markdown.append("| Metric | Value |")
    markdown.append("| :--- | :--- |")
    for k, v in agg.items():
        if "latency" in k:
            markdown.append(f"| {k} | {v:.4f}s |")
        else:
            markdown.append(f"| {k} | {v:.4%} |")
    markdown.append("")
    if "evaluated_question_count" in data:
        markdown.append("## Evaluation Scope")
        markdown.append(f"- Evaluated questions: `{data['evaluated_question_count']}`")
        markdown.append(
            f"- Skipped empty-gold-evidence questions: `{data.get('skipped_empty_gold_evidence_count', 0)}`"
        )
        markdown.append("")

    markdown.append("## Failure Analysis (Top 30 Examples)")
    markdown.append("Questions where Recall@10 was less than 100%.")
    markdown.append("")

    failures = [r for r in results if r["metrics"].get("recall@10", 1.0) < 1.0]
    failures = failures[:30]

    for i, f in enumerate(failures):
        markdown.append(f"### {i+1}. Question: {f['question']}")
        markdown.append(f"- **Doc ID**: {f['doc_id']}")
        markdown.append(f"- **Recall@10**: {f['metrics'].get('recall@10', 0):.2%}")
        markdown.append(f"- **Gold Evidence**: `{', '.join(f['gold_evidence'])}`")
        markdown.append(f"- **Top 10 Retrieved IDs**: `{', '.join(f['top_10_results'])}`")
        markdown.append("")

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(markdown), encoding="utf-8")
    print(f"Report generated at {output_md}")


def main():
    parser = argparse.ArgumentParser(description="QASPER Step 05: Generate Report.")
    parser.add_argument(
        "--metrics-path",
        "--metrics-json",
        dest="metrics_path",
        type=Path,
        default=Path("reports/qasper_metrics.json"),
    )
    parser.add_argument(
        "--report-path",
        "--output-md",
        dest="report_path",
        type=Path,
        default=Path("reports/final_report.md"),
    )
    args = parser.parse_args()

    run_step05(metrics_json=args.metrics_path, output_md=args.report_path)


if __name__ == "__main__":
    main()
