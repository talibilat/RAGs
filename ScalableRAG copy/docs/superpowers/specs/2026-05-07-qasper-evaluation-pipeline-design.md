# QASPER Evaluation Pipeline Design

> **Status:** Draft
> **Date:** 2026-05-07
> **Topic:** Comprehensive design for the QASPER retrieval benchmark pipeline.

## 1. Objective
Implement a robust, modular, and reproducible retrieval evaluation pipeline using the QASPER dataset. The pipeline must measure the performance of the ScalableRAG dual-engine retrieval plane (OpenSearch + Qdrant + Cohere Rerank) against human-annotated ground truth.

## 2. Approach: Stepwise Pipeline
We will implement the benchmark as a series of discrete scripts (`qasper_step01` through `qasper_step05`). This approach ensures:
- **Modularity**: Each stage can be run and debugged independently.
- **Cost Efficiency**: Expensive Azure DI parsing and embedding results are cached on disk.
- **Observability**: Intermediate artifacts (ledger entries, markdown files, indices) can be inspected.

## 3. Configuration
A new setting `QASPER_EVAL_LIMIT` will be added to the `.env` file (default: `50`). This parameter controls the number of documents processed during the ingestion and evaluation phases.

## 4. Components

### Step 01: Ingestion (`qasper_step01_ingest.py`)
- **Input**: `data/manifest.json`.
- **Logic**:
    - Load the manifest.
    - Randomly sample `QASPER_EVAL_LIMIT` documents using a fixed seed (`42`).
    - Register each sampled PDF into the PostgreSQL ledger using `ingest_file`.
- **Output**: Ledger entries with `status='PENDING'`.

### Step 02: Extraction (`qasper_step02_parse.py`)
- **Input**: Ledger documents with `status='PENDING'`.
- **Logic**:
    - Iterate through pending documents.
    - Use `AzureParser` to extract structured Markdown and page-level metadata.
- **Output**: Markdown files in `data/processed/pdf_text/{doc_id}.md` and status updated to `'PARSED'`.

### Step 03: Indexing (`qasper_step03_index.py`)
- **Input**: Markdown files from Step 02.
- **Logic**:
    - Chunk documents using three strategies:
        1. `fixed_300_overlap_50`
        2. `fixed_600_overlap_100`
        3. `section_aware` (utilizing Markdown headers).
    - Insert chunks into **OpenSearch** (BM25) and **Qdrant** (Dense vectors via Azure OpenAI).
- **Output**: Populated retrieval indices.

### Step 04: Evaluation (`qasper_step04_eval.py`)
- **Input**: `data/eval/qasper_qa_gold.jsonl`.
- **Logic**:
    - Filter ground truth questions for the sampled 50 documents.
    - Execute the retrieval pipeline: Hybrid Search (RRF) -> Cohere Reranking.
    - Compare retrieved chunks against `gold_evidence`.
    - Calculate Recall@1, @5, @10, MRR@10, nDCG@10.
    - Capture p50/p95/p99 latency.
- **Output**: `reports/qasper_metrics.json`.

### Step 05: Reporting (`qasper_step05_report.py`)
- **Input**: `reports/qasper_metrics.json`.
- **Logic**:
    - Format results into a human-readable Markdown report.
    - Include 30 failure analysis examples (questions where Recall@10 failed).
- **Output**: `reports/final_report.md`.

## 5. Success Criteria
- Successful ingestion of $N$ documents into the ledger.
- Generation of high-quality Markdown via Azure DI.
- Successful indexing into OpenSearch and Qdrant.
- Production of an evaluation report with deterministic IR metrics.
