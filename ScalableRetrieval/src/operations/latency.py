from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Awaitable, Callable


LoadTestRetriever = Callable[[str], Awaitable[list[dict]]]


@dataclass(frozen=True)
class LatencySample:
    query_id: str
    latency_ms: float
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class LatencySummary:
    query_count: int
    success_count: int
    error_count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    samples: tuple[LatencySample, ...]


def calculate_latency_summary(samples: list[LatencySample]) -> LatencySummary:
    successful_latencies = sorted(sample.latency_ms for sample in samples if sample.ok)
    return LatencySummary(
        query_count=len(samples),
        success_count=len(successful_latencies),
        error_count=sum(1 for sample in samples if not sample.ok),
        p50_ms=_nearest_rank(successful_latencies, 50),
        p95_ms=_nearest_rank(successful_latencies, 95),
        p99_ms=_nearest_rank(successful_latencies, 99),
        samples=tuple(samples),
    )


async def run_load_test(
    retriever: LoadTestRetriever,
    *,
    query_count: int = 100,
    concurrency: int = 25,
) -> LatencySummary:
    semaphore = asyncio.Semaphore(concurrency)
    samples: list[LatencySample] = []

    async def run_one(index: int) -> None:
        query_id = f"load-query-{index:03d}"
        async with semaphore:
            started = time.perf_counter()
            try:
                await retriever(query_id)
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - started) * 1000
                samples.append(
                    LatencySample(
                        query_id=query_id,
                        latency_ms=elapsed_ms,
                        ok=False,
                        error=str(exc),
                    )
                )
            else:
                elapsed_ms = (time.perf_counter() - started) * 1000
                samples.append(
                    LatencySample(query_id=query_id, latency_ms=elapsed_ms, ok=True)
                )

    await asyncio.gather(*(run_one(index) for index in range(1, query_count + 1)))
    samples.sort(key=lambda sample: sample.query_id)
    return calculate_latency_summary(samples)


def write_latency_report(summary: LatencySummary, path: Path) -> None:
    payload = {
        "query_count": summary.query_count,
        "success_count": summary.success_count,
        "error_count": summary.error_count,
        "latency_ms": {
            "p50": summary.p50_ms,
            "p95": summary.p95_ms,
            "p99": summary.p99_ms,
        },
        "samples": [asdict(sample) for sample in summary.samples],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def build_fixture_retriever() -> LoadTestRetriever:
    async def retrieve(query_id: str) -> list[dict]:
        await asyncio.sleep(0)
        return [{"id": query_id, "text": "fixture result"}]

    return retrieve


def build_live_retriever() -> LoadTestRetriever:
    from src.retrieval.dual_engine import dual_search, rerank_results

    async def retrieve(query_id: str) -> list[dict]:
        query = f"operational load test query {query_id}"
        query_vector = [0.1, 0.2, 0.3, 0.4]
        candidates = await dual_search(query, query_vector, "tenant_integration_test", k=10)
        return await rerank_results(query, candidates)

    return retrieve


async def run_latency_report(
    *,
    output_path: Path,
    query_count: int,
    concurrency: int,
    backend: str,
) -> LatencySummary:
    if backend == "fixture":
        retriever = build_fixture_retriever()
    elif backend == "live":
        retriever = build_live_retriever()
    else:
        raise ValueError("backend must be 'fixture' or 'live'")

    summary = await run_load_test(
        retriever,
        query_count=query_count,
        concurrency=concurrency,
    )
    write_latency_report(summary, output_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Step 08 retrieval latency load test.")
    parser.add_argument("--output", type=Path, default=Path("evidence/step08/latency_report.json"))
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=25)
    parser.add_argument("--backend", choices=("fixture", "live"), default="fixture")
    args = parser.parse_args()

    summary = asyncio.run(
        run_latency_report(
            output_path=args.output,
            query_count=args.queries,
            concurrency=args.concurrency,
            backend=args.backend,
        )
    )
    print(
        "query_count={query_count} success_count={success_count} "
        "error_count={error_count} p50_ms={p50:.3f} p95_ms={p95:.3f} p99_ms={p99:.3f}".format(
            query_count=summary.query_count,
            success_count=summary.success_count,
            error_count=summary.error_count,
            p50=summary.p50_ms,
            p95=summary.p95_ms,
            p99=summary.p99_ms,
        )
    )


def _nearest_rank(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    rank = math.ceil((percentile / 100) * len(values))
    return values[max(0, rank - 1)]


if __name__ == "__main__":
    main()
