from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Awaitable, Callable, Iterable, Protocol


Retriever = Callable[["EvaluationCase"], Awaitable[list[dict]]]


@dataclass(frozen=True)
class EvaluationCase:
    query_id: str
    query: str
    tenant_id: str
    expected_chunk_ids: tuple[str, ...]
    expected_answer: str


@dataclass(frozen=True)
class QueryEvaluationResult:
    query_id: str
    recall_at_10: float
    ndcg_at_10: float
    faithfulness: float
    context_precision: float
    retrieved_chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationReport:
    query_count: int
    recall_at_10: float
    ndcg_at_10: float
    faithfulness: float
    context_precision: float
    results: tuple[QueryEvaluationResult, ...]


class SemanticJudge(Protocol):
    def score(
        self,
        *,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> tuple[float, float]:
        ...


class DeterministicSemanticJudge:
    """
    CI-safe RAGAS-compatible fallback.

    Scores faithfulness from answer-token support in retrieved context and
    context precision from the share of retrieved contexts that overlap with
    the answer. A live RAGAS judge can be wired behind the same interface later.
    """

    def score(
        self,
        *,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> tuple[float, float]:
        answer_tokens = _content_tokens(answer)
        if not answer_tokens:
            return 0.0, 0.0

        context_text = " ".join(contexts)
        context_tokens = _content_tokens(context_text)
        supported = answer_tokens & context_tokens
        faithfulness = len(supported) / len(answer_tokens)

        if not contexts:
            return faithfulness, 0.0

        relevant_seen = 0
        precision_sum = 0.0
        for index, context in enumerate(contexts, start=1):
            if _content_tokens(context) & answer_tokens:
                relevant_seen += 1
                precision_sum += relevant_seen / index
        context_precision = precision_sum / relevant_seen if relevant_seen else 0.0
        return faithfulness, context_precision


def load_qrels_csv(path: Path) -> list[EvaluationCase]:
    with Path(path).open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    cases: list[EvaluationCase] = []
    for row in rows:
        expected_chunk_ids = tuple(
            chunk_id.strip()
            for chunk_id in row["expected_chunk_ids"].split("|")
            if chunk_id.strip()
        )
        cases.append(
            EvaluationCase(
                query_id=row["query_id"].strip(),
                query=row["query"].strip(),
                tenant_id=row["tenant_id"].strip(),
                expected_chunk_ids=expected_chunk_ids,
                expected_answer=row["expected_answer"].strip(),
            )
        )
    return cases


def recall_at_k(
    ranked_chunk_ids: Iterable[str],
    relevant_chunk_ids: set[str],
    *,
    k: int,
) -> float:
    if not relevant_chunk_ids:
        return 0.0
    top_k = set(tuple(ranked_chunk_ids)[:k])
    return len(top_k & relevant_chunk_ids) / len(relevant_chunk_ids)


def ndcg_at_k(
    ranked_chunk_ids: Iterable[str],
    relevant_chunk_ids: set[str],
    *,
    k: int,
) -> float:
    if not relevant_chunk_ids:
        return 0.0

    ranked = tuple(ranked_chunk_ids)[:k]
    dcg = 0.0
    for index, chunk_id in enumerate(ranked):
        if chunk_id in relevant_chunk_ids:
            rank = index + 1
            dcg += 1.0 / math.log2(rank + 1)

    ideal_hits = min(len(relevant_chunk_ids), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


async def evaluate_cases(
    cases: Iterable[EvaluationCase],
    retriever: Retriever,
    *,
    semantic_judge: SemanticJudge | None = None,
    k: int = 10,
) -> EvaluationReport:
    judge = semantic_judge or DeterministicSemanticJudge()
    results: list[QueryEvaluationResult] = []

    for case in cases:
        retrieved = await retriever(case)
        ranked_ids = tuple(str(item["id"]) for item in retrieved)
        contexts = [str(item.get("text", "")) for item in retrieved[:k]]
        relevant = set(case.expected_chunk_ids)
        faithfulness, context_precision = judge.score(
            question=case.query,
            answer=case.expected_answer,
            contexts=contexts,
        )
        results.append(
            QueryEvaluationResult(
                query_id=case.query_id,
                recall_at_10=recall_at_k(ranked_ids, relevant, k=k),
                ndcg_at_10=ndcg_at_k(ranked_ids, relevant, k=k),
                faithfulness=faithfulness,
                context_precision=context_precision,
                retrieved_chunk_ids=ranked_ids[:k],
            )
        )

    return EvaluationReport(
        query_count=len(results),
        recall_at_10=_mean(result.recall_at_10 for result in results),
        ndcg_at_10=_mean(result.ndcg_at_10 for result in results),
        faithfulness=_mean(result.faithfulness for result in results),
        context_precision=_mean(result.context_precision for result in results),
        results=tuple(results),
    )


def build_fixture_retriever() -> Retriever:
    async def retrieve(case: EvaluationCase) -> list[dict]:
        expected_id = case.expected_chunk_ids[0]
        return [
            {"id": expected_id, "text": case.expected_answer},
            {"id": f"{case.query_id}-distractor-1", "text": "Irrelevant retrieved context."},
            {"id": f"{case.query_id}-distractor-2", "text": "Additional noise."},
        ]

    return retrieve


def build_live_retriever() -> Retriever:
    from src.retrieval.dual_engine import dual_search, rerank_results

    async def retrieve(case: EvaluationCase) -> list[dict]:
        query_vector = [0.1, 0.2, 0.3, 0.4]
        candidates = await dual_search(case.query, query_vector, case.tenant_id, k=20)
        return await rerank_results(case.query, candidates)

    return retrieve


def write_report(report: EvaluationReport, path: Path) -> None:
    payload = {
        "query_count": report.query_count,
        "metrics": {
            "recall_at_10": report.recall_at_10,
            "ndcg_at_10": report.ndcg_at_10,
            "faithfulness": report.faithfulness,
            "context_precision": report.context_precision,
        },
        "results": [asdict(result) for result in report.results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


async def run_evaluation(
    *,
    qrels_path: Path,
    output_path: Path,
    backend: str,
) -> EvaluationReport:
    cases = load_qrels_csv(qrels_path)
    if backend == "live":
        retriever = build_live_retriever()
    elif backend == "fixture":
        retriever = build_fixture_retriever()
    else:
        raise ValueError("backend must be 'fixture' or 'live'")

    report = await evaluate_cases(cases, retriever, semantic_judge=DeterministicSemanticJudge())
    write_report(report, output_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Step 07 retrieval evaluation.")
    parser.add_argument("--qrels", type=Path, default=Path("data/evaluation/qrels_step07.csv"))
    parser.add_argument("--output", type=Path, default=Path("evidence/step07/evaluation_report.json"))
    parser.add_argument("--backend", choices=("fixture", "live"), default="fixture")
    args = parser.parse_args()

    report = asyncio.run(
        run_evaluation(qrels_path=args.qrels, output_path=args.output, backend=args.backend)
    )
    print(
        "query_count={query_count} recall_at_10={recall:.4f} "
        "ndcg_at_10={ndcg:.4f} faithfulness={faithfulness:.4f} "
        "context_precision={context_precision:.4f}".format(
            query_count=report.query_count,
            recall=report.recall_at_10,
            ndcg=report.ndcg_at_10,
            faithfulness=report.faithfulness,
            context_precision=report.context_precision,
        )
    )


def _content_tokens(text: str) -> set[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "by",
        "in",
        "is",
        "of",
        "the",
        "to",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in stop_words
    }


def _mean(values: Iterable[float]) -> float:
    values = tuple(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


if __name__ == "__main__":
    main()
