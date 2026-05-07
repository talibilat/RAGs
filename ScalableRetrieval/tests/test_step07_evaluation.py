"""
Plan 07 - Evaluation and Telemetry

Evidence required by plan/07-evaluation-and-telemetry.md:
  1. A 50-query qrels dataset.
  2. CI-ready deterministic evaluation metrics.
  3. A report containing Recall@10, NDCG@10, Faithfulness, and Context Precision.
"""
import json
from pathlib import Path

import pytest

from src.evaluation.evaluator import (
    DeterministicSemanticJudge,
    EvaluationCase,
    evaluate_cases,
    load_qrels_csv,
    ndcg_at_k,
    recall_at_k,
    write_report,
)


def test_qrels_dataset_contains_50_queries_with_expected_chunk_ids():
    cases = load_qrels_csv(Path("data/evaluation/qrels_step07.csv"))

    assert len(cases) == 50
    assert all(case.query_id for case in cases)
    assert all(case.query for case in cases)
    assert all(case.tenant_id for case in cases)
    assert all(case.expected_chunk_ids for case in cases)
    assert len({case.query_id for case in cases}) == 50


def test_recall_at_10_returns_one_when_relevant_chunk_is_in_top_10():
    ranked_chunk_ids = [f"chunk-{idx}" for idx in range(1, 12)]

    assert recall_at_k(ranked_chunk_ids, {"chunk-10"}, k=10) == 1.0
    assert recall_at_k(ranked_chunk_ids, {"chunk-11"}, k=10) == 0.0


def test_ndcg_at_10_rewards_higher_ranked_relevant_chunks():
    best = ndcg_at_k(["gold", "other"], {"gold"}, k=10)
    lower = ndcg_at_k(["other", "gold"], {"gold"}, k=10)
    missing = ndcg_at_k(["other"], {"gold"}, k=10)

    assert best == 1.0
    assert 0.0 < lower < best
    assert missing == 0.0


@pytest.mark.asyncio
async def test_evaluate_cases_calculates_deterministic_and_semantic_metrics():
    cases = [
        EvaluationCase(
            query_id="q1",
            query="What policy governs refunds?",
            tenant_id="tenant_eval",
            expected_chunk_ids=("chunk-a",),
            expected_answer="Refunds are governed by the billing policy.",
        ),
        EvaluationCase(
            query_id="q2",
            query="Where is escalation documented?",
            tenant_id="tenant_eval",
            expected_chunk_ids=("chunk-b",),
            expected_answer="Escalation is documented in the support runbook.",
        ),
    ]

    async def retriever(case: EvaluationCase):
        if case.query_id == "q1":
            return [
                {"id": "chunk-a", "text": "Refunds are governed by the billing policy."},
                {"id": "chunk-x", "text": "Noise"},
            ]
        return [
            {"id": "chunk-x", "text": "Noise"},
            {"id": "chunk-b", "text": "Escalation is documented in the support runbook."},
        ]

    report = await evaluate_cases(cases, retriever, semantic_judge=DeterministicSemanticJudge())

    assert report.query_count == 2
    assert report.recall_at_10 == 1.0
    assert round(report.ndcg_at_10, 4) == 0.8155
    assert report.faithfulness == 1.0
    assert report.context_precision == 0.75
    assert report.results[0].retrieved_chunk_ids == ("chunk-a", "chunk-x")


def test_write_report_outputs_required_metrics(tmp_path):
    case = EvaluationCase(
        query_id="q1",
        query="What policy governs refunds?",
        tenant_id="tenant_eval",
        expected_chunk_ids=("chunk-a",),
        expected_answer="Refunds are governed by the billing policy.",
    )

    class DummyReport:
        query_count = 1
        recall_at_10 = 1.0
        ndcg_at_10 = 1.0
        faithfulness = 1.0
        context_precision = 1.0
        results = []

    output_path = tmp_path / "report.json"
    write_report(DummyReport(), output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["query_count"] == 1
    assert payload["metrics"]["recall_at_10"] == 1.0
    assert payload["metrics"]["ndcg_at_10"] == 1.0
    assert payload["metrics"]["faithfulness"] == 1.0
    assert payload["metrics"]["context_precision"] == 1.0
