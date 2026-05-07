import argparse
import asyncio
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Set

from tqdm import tqdm

from src.config.settings import settings
from src.ingestion.embedding import AzureEmbeddingClient
from src.ledger.models import ChunkEmbedding, Document, DocumentVersion
from src.parsing.parse import build_session_factory_from_url
from src.retrieval.dual_engine import dual_search, rerank_results
from sqlalchemy import select


def get_sampled_doc_ids(session_factory) -> Set[str]:
    with session_factory() as session:
        docs = session.scalars(
            select(Document)
            .join(DocumentVersion)
            .join(ChunkEmbedding, ChunkEmbedding.document_version_id == DocumentVersion.id)
            .where(Document.tenant_id == "qasper_eval")
            .distinct()
        ).all()
        return {d.filename.replace(".pdf", "") for d in docs}


def calculate_metrics(
    results: List[Dict[str, Any]],
    gold_evidence: List[str],
    *,
    evidence_match_threshold: float = 0.55,
) -> Dict[str, float]:
    k_values = [1, 5, 10]
    metrics = {f"recall@{k}": 0.0 for k in k_values}
    metrics["mrr@10"] = 0.0

    if not gold_evidence:
        return metrics

    # Recall@K
    for k in k_values:
        top_k_results = results[:k]
        hits = 0
        for ge in gold_evidence:
            if any(
                _evidence_matches_result(
                    ge,
                    result,
                    evidence_match_threshold=evidence_match_threshold,
                )
                for result in top_k_results
            ):
                hits += 1
        metrics[f"recall@{k}"] = hits / len(gold_evidence)

    # MRR@10
    for rank, result in enumerate(results[:10]):
        if any(
            _evidence_matches_result(
                ge,
                result,
                evidence_match_threshold=evidence_match_threshold,
            )
            for ge in gold_evidence
        ):
            metrics["mrr@10"] = 1.0 / (rank + 1)
            break

    return metrics


def _evidence_matches_result(
    gold_evidence: str,
    result: Dict[str, Any],
    *,
    evidence_match_threshold: float,
) -> bool:
    evidence = gold_evidence.strip()
    if not evidence:
        return False

    # Backwards compatibility for qrels that store expected chunk IDs.
    if evidence == str(result.get("id", "")).strip():
        return True

    retrieved_text = str(result.get("text", ""))
    if not retrieved_text:
        return False

    normalized_evidence = _normalize_evidence_text(evidence)
    normalized_text = _normalize_evidence_text(retrieved_text)
    if normalized_evidence in normalized_text:
        return True

    evidence_tokens = _content_tokens(normalized_evidence)
    if not evidence_tokens:
        return False

    retrieved_tokens = _content_tokens(normalized_text)
    coverage = len(evidence_tokens & retrieved_tokens) / len(evidence_tokens)
    return coverage >= evidence_match_threshold


def _normalize_evidence_text(text: str) -> str:
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.casefold().strip()


def _content_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


async def run_eval_async(
    gold_path: Path,
    report_path: Path,
    database_url: str,
):
    session_factory = build_session_factory_from_url(database_url)
    sampled_doc_ids = get_sampled_doc_ids(session_factory)
    tqdm.write(f"Loaded {len(sampled_doc_ids)} indexed document IDs.")

    embed_client = AzureEmbeddingClient(
        endpoint=settings.AZURE_OPENAI_ENDPOINT or "",
        key=settings.AZURE_OPENAI_KEY or "",
        deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )

    questions = []
    skipped_empty_gold = 0
    with gold_path.open("r", encoding="utf-8") as f:
        for line in f:
            q = json.loads(line)
            if q["doc_id"] in sampled_doc_ids:
                if not q.get("gold_evidence"):
                    skipped_empty_gold += 1
                    continue
                questions.append(q)

    tqdm.write(f"Evaluating {len(questions)} questions...")

    results_data = []
    latencies = []

    progress = tqdm(
        questions,
        total=len(questions),
        desc="Evaluating questions",
        unit="question",
        dynamic_ncols=True,
    )
    for index, q in enumerate(progress, start=1):
        start_time = time.perf_counter()
        
        # 1. Embed query
        query_vector = embed_client.embed_chunks([q["question"]])[0]
        
        # 2. Dual Search (BM25 + Vector)
        candidates = await dual_search(
            query=q["question"],
            query_vector=query_vector,
            tenant_id="qasper_eval",
            k=50,
            doc_id=q["doc_id"],
        )
        
        # 3. Rerank
        reranked = await rerank_results(q["question"], candidates)
        
        latency = time.perf_counter() - start_time
        latencies.append(latency)

        # 4. Score
        metrics = calculate_metrics(reranked, q["gold_evidence"])
        running_recall_at_10 = (
            (sum(r["metrics"]["recall@10"] for r in results_data) + metrics["recall@10"])
            / index
        )
        if hasattr(progress, "set_postfix"):
            progress.set_postfix(
                {
                    "doc": q["doc_id"],
                    "query": q["query_id"],
                    "latency_s": f"{latency:.2f}",
                    "recall@10": f"{running_recall_at_10:.3f}",
                }
            )
        
        results_data.append({
            "question_id": q["query_id"],
            "question": q["question"],
            "doc_id": q["doc_id"],
            "metrics": metrics,
            "latency": latency,
            "top_10_results": [r["id"] for r in reranked[:10]],
            "gold_evidence": q["gold_evidence"]
        })

    # Aggregate metrics
    agg_metrics = {}
    if results_data:
        for key in results_data[0]["metrics"].keys():
            agg_metrics[key] = sum(r["metrics"][key] for r in results_data) / len(results_data)
        
        agg_metrics["avg_latency"] = sum(latencies) / len(latencies)
        import numpy as np
        agg_metrics["p50_latency"] = float(np.percentile(latencies, 50))
        agg_metrics["p95_latency"] = float(np.percentile(latencies, 95))
        agg_metrics["p99_latency"] = float(np.percentile(latencies, 99))

    report = {
        "aggregate_metrics": agg_metrics,
        "evaluated_question_count": len(results_data),
        "skipped_empty_gold_evidence_count": skipped_empty_gold,
        "individual_results": results_data
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    tqdm.write(f"Evaluation complete. Report saved to {report_path}")
    tqdm.write(f"Recall@10: {agg_metrics.get('recall@10', 0):.4f}")


def run_step04(
    gold_path: Path,
    report_path: Path,
    database_url: str = settings.postgres_dsn,
):
    asyncio.run(run_eval_async(gold_path, report_path, database_url))


def main():
    parser = argparse.ArgumentParser(description="QASPER Step 04: Evaluate Retrieval.")
    parser.add_argument("--gold-path", type=Path, default=Path("data/eval/qasper_qa_gold.jsonl"))
    parser.add_argument("--report-path", type=Path, default=Path("reports/qasper_metrics.json"))
    args = parser.parse_args()

    run_step04(gold_path=args.gold_path, report_path=args.report_path)


if __name__ == "__main__":
    main()
