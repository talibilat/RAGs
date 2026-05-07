# QASPER Dataset and Evaluation README

This repository currently has Step 00 completed: QASPER dataset acquisition, PDF preparation, manifest creation, and QA/evidence ground-truth normalization.

The full QASPER retrieval benchmark is not completed yet. The remaining work is to parse the prepared PDFs, chunk them, build indexes, retrieve evidence chunks, and score retrieval results against `data/eval/qasper_qa_gold.jsonl`.

## Current Step 00 Outputs

Step 00 produced the following artifacts:

- `data/raw/qasper/` - official QASPER split files and download metadata.
- `data/raw/pdfs/original/` - legally accessible original PDFs.
- `data/raw/pdfs/generated/` - fallback PDFs generated from QASPER structured full text.
- `data/processed/qasper_documents.jsonl` - normalized document records.
- `data/processed/qasper_qa_gold.jsonl` - normalized QA/evidence rows.
- `data/eval/qasper_qa_gold.jsonl` - evaluation ground truth for future retrieval evaluation.
- `data/manifest.json` - canonical document-to-PDF manifest with checksums and provenance.
- `reports/pdf_resolution_failures.jsonl` - original PDF resolution failures that required generated fallback PDFs.
- `reports/step00_dataset_summary.json` - machine-readable dataset summary.
- `reports/step00_dataset_summary.md` - human-readable dataset summary.

Current dataset summary:

- QASPER documents: `1,585`
- Usable PDFs: `1,585`
- Original PDFs downloaded: `1,580`
- Generated fallback PDFs: `5`
- Questions: `5,049`
- Answer annotations: `7,993`
- Evidence annotations: `9,921`
- Validation errors: `0`

Generated PDFs are explicitly marked as generated in `data/manifest.json`. Do not treat them as original publisher PDFs.

## Environment Setup

From the repository root:

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
```

If your environment already has dependencies installed, you can skip the install step.

## Run Step 00 From Terminal

To reproduce the full QASPER dataset package:

```bash
make step00-qasper
```

Equivalent direct command:

```bash
venv/bin/python -m src.datasets.qasper_step00 --root .
```

This downloads QASPER from `allenai/qasper`, attempts open original PDF resolution, generates fallback PDFs where needed, writes the manifest, and writes the summary reports.

For a faster local check that avoids original PDF downloads and generates PDFs from QASPER structured text:

```bash
venv/bin/python -m src.datasets.qasper_step00 \
  --root . \
  --skip-original-pdf-downloads \
  --min-usable-pdfs 1000
```

Use this only as a reproducibility smoke test. The production dataset package should attempt original PDF resolution.

## Validate Step 00

Run the focused Step 00 tests:

```bash
pytest tests/test_step00_qasper_dataset.py -q
```

Check the generated summary:

```bash
python - <<'PY'
import json

summary = json.load(open("reports/step00_dataset_summary.json"))
for key in [
    "total_qasper_documents",
    "total_usable_pdfs",
    "original_pdfs_downloaded",
    "fallback_pdfs_generated",
    "failed_documents",
    "total_questions",
    "total_answer_annotations",
    "total_evidence_annotations",
    "validation_errors",
]:
    print(key, summary[key])
PY
```

Check manifest and evaluation row counts:

```bash
python - <<'PY'
import json

manifest = json.load(open("data/manifest.json"))
qa_rows = sum(1 for _ in open("data/eval/qasper_qa_gold.jsonl"))
print("manifest_documents", len(manifest["documents"]))
print("eval_rows", qa_rows)
PY
```

Expected values for the completed Step 00 run:

- `manifest_documents`: `1585`
- `eval_rows`: `5049`
- `validation_errors`: `[]`

## Existing Fixture Evaluation

The repository still contains an older fixture-style evaluator in `src/evaluation/evaluator.py`. It does not yet evaluate QASPER PDF retrieval quality.

You can run the existing fixture evaluation with:

```bash
venv/bin/python -m src.evaluation.evaluator \
  --qrels data/evaluation/qrels_step07.csv \
  --output evidence/step07/evaluation_report.json \
  --backend fixture
```

That command is useful only for checking the legacy metric plumbing. It is not the final QASPER benchmark because it uses CSV fixture qrels rather than `data/eval/qasper_qa_gold.jsonl`.

## Remaining Work

The whole retrieval platform is not complete yet. Step 00 is complete; the following parts remain:

1. PDF ingestion from `data/manifest.json`.
2. PDF text extraction with page-level metadata under `data/processed/pdf_text/`.
3. Incremental indexing using PDF and chunk hashes.
4. Chunking strategies:
   - `fixed_300_overlap_50`
   - `fixed_600_overlap_100`
   - `section_aware`
5. BM25 indexing.
6. Dense vector indexing.
7. Hybrid retrieval with Reciprocal Rank Fusion.
8. Modular reranking over top hybrid candidates.
9. QASPER retrieval evaluation using `data/eval/qasper_qa_gold.jsonl`.
10. Metrics:
    - document Recall@1, @5, @10
    - evidence Recall@1, @5, @10
    - MRR@10
    - nDCG@10
    - p50 latency
    - p95 latency
    - p99 latency
11. Failure analysis with at least 30 examples.
12. Final reports:
    - `reports/final_report.md`
    - `reports/final_report.pdf`

## Recommended Next Command

Before implementing the remaining benchmark, confirm Step 00 artifacts are still valid:

```bash
pytest tests/test_step00_qasper_dataset.py -q
```

Then implement the next stage: PDF text extraction from every manifest entry into `data/processed/pdf_text/`.
