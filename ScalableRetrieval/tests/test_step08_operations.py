"""
Plan 08 - Operations and Final Evidence

Evidence required by plan/08-operations-and-evidence.md:
  1. Retrieval latency report with P50/P95/P99.
  2. Reproducible reset command.
  3. Final evidence pack manifest aggregating required artifacts.
"""
import asyncio
import json
from pathlib import Path

import pytest

from src.operations.evidence_pack import compile_evidence_pack
from src.operations.latency import (
    LatencySample,
    calculate_latency_summary,
    run_load_test,
    write_latency_report,
)
from src.operations.seed_documents import seed_documents


def test_calculate_latency_summary_uses_nearest_rank_percentiles():
    samples = [
        LatencySample(query_id=f"q{idx:03d}", latency_ms=float(idx), ok=True)
        for idx in range(1, 101)
    ]

    summary = calculate_latency_summary(samples)

    assert summary.query_count == 100
    assert summary.success_count == 100
    assert summary.error_count == 0
    assert summary.p50_ms == 50.0
    assert summary.p95_ms == 95.0
    assert summary.p99_ms == 99.0


@pytest.mark.asyncio
async def test_run_load_test_executes_concurrent_queries():
    active = 0
    max_active = 0

    async def retriever(query_id: str):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        try:
            await asyncio.sleep(0)
            return [{"id": query_id, "text": "ok"}]
        finally:
            active -= 1

    summary = await run_load_test(
        retriever,
        query_count=100,
        concurrency=25,
    )

    assert summary.query_count == 100
    assert summary.success_count == 100
    assert summary.error_count == 0
    assert max_active == 25
    assert summary.p50_ms >= 0.0
    assert len(summary.samples) == 100


def test_write_latency_report_outputs_required_slo_fields(tmp_path):
    summary = calculate_latency_summary(
        [
            LatencySample(query_id="q1", latency_ms=10.0, ok=True),
            LatencySample(query_id="q2", latency_ms=20.0, ok=True),
        ]
    )
    output_path = tmp_path / "latency.json"

    write_latency_report(summary, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["query_count"] == 2
    assert payload["success_count"] == 2
    assert payload["latency_ms"]["p50"] == 10.0
    assert payload["latency_ms"]["p95"] == 20.0
    assert payload["latency_ms"]["p99"] == 20.0


def test_compile_evidence_pack_writes_manifest(tmp_path):
    repo_root = tmp_path
    (repo_root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (repo_root / ".env.example").write_text("POSTGRES_USER=postgres\n", encoding="utf-8")
    (repo_root / "evidence" / "step00").mkdir(parents=True)
    (repo_root / "evidence" / "step00" / "docker_compose_ps.log").write_text(
        "postgres healthy\nredis healthy\nopensearch healthy\nqdrant healthy\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step00" / "config_loader.log").write_text(
        "Environment configuration successfully loaded and validated.\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step01").mkdir(parents=True)
    (repo_root / "evidence" / "step01" / "first_ingestion.log").write_text(
        "seen=10 created=10 skipped_duplicates=0\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step01" / "duplicate_ingestion.log").write_text(
        "seen=10 created=0 skipped_duplicates=10\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step01" / "postgres_counts.log").write_text(
        "documents=10\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step02").mkdir(parents=True)
    (repo_root / "evidence" / "step02" / "parsed_markdown_sample.md").write_text(
        "| Name | Revenue |\n| - | -: |\n| Alpha | 10 |\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step02" / "parse_status.log").write_text(
        "pending -> parsed\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step03").mkdir(parents=True)
    (repo_root / "evidence" / "step03" / "zero_waste_embeddings.log").write_text(
        "new_embeddings=0\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step04").mkdir(parents=True)
    (repo_root / "evidence" / "step04" / "worker_sync.log").write_text(
        "OpenSearch upsert\nQdrant upsert\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step05").mkdir(parents=True)
    (repo_root / "evidence" / "step05" / "retrieval_rerank.log").write_text(
        "dual_search\nReranked output\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step06").mkdir(parents=True)
    (repo_root / "evidence" / "step06" / "red_team_test.log").write_text(
        "Content Blocked\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step06" / "structured_prompt_template.txt").write_text(
        "<untrusted_context>\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step07").mkdir(parents=True)
    (repo_root / "evidence" / "step07" / "evaluation_report.json").write_text(
        '{"metrics":{"recall_at_10":1.0}}\n',
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step08").mkdir(parents=True)
    (repo_root / "evidence" / "step08" / "postgres_ledger_1000_dump.log").write_text(
        "documents=1000\n",
        encoding="utf-8",
    )
    (repo_root / "evidence" / "step08" / "latency_report.json").write_text(
        '{"latency_ms":{"p50":1.0,"p95":2.0,"p99":3.0}}\n',
        encoding="utf-8",
    )

    manifest = compile_evidence_pack(repo_root, repo_root / "evidence" / "final")

    assert manifest.output_dir == repo_root / "evidence" / "final"
    assert manifest.missing_artifacts == ()
    assert "docker-compose.yml" in manifest.included_artifacts
    assert "step00/docker_compose_ps.log" in manifest.included_artifacts
    assert "step02/parsed_markdown_sample.md" in manifest.included_artifacts
    assert "step04/worker_sync.log" in manifest.included_artifacts
    assert "step05/retrieval_rerank.log" in manifest.included_artifacts
    assert "step08/postgres_ledger_1000_dump.log" in manifest.included_artifacts
    assert "step08/latency_report.json" in manifest.included_artifacts
    manifest_payload = json.loads(
        (repo_root / "evidence" / "final" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest_payload["complete"] is True


def test_makefile_contains_reset_target():
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "reset:" in makefile
    assert "docker compose down -v --remove-orphans" in makefile
    assert "docker compose up -d --build" in makefile


def test_qdrant_healthcheck_uses_available_bash_tcp_probe():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "wget -qO- http://localhost:6333/readyz" not in compose
    assert "bash -c" in compose
    assert "/dev/tcp/localhost/6333" in compose


def test_seed_documents_creates_unique_pdfs_and_skips_reruns(tmp_path):
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from src.ledger.models import Base, Document

    engine = create_engine(f"sqlite:///{tmp_path / 'ledger.db'}", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)

    first = seed_documents(
        source_dir=tmp_path / "incoming",
        storage_dir=tmp_path / "raw",
        tenant_id="tenant-seed",
        count=5,
        session_factory=session_factory,
    )
    second = seed_documents(
        source_dir=tmp_path / "incoming",
        storage_dir=tmp_path / "raw",
        tenant_id="tenant-seed",
        count=5,
        session_factory=session_factory,
    )

    assert first.created == 5
    assert first.skipped_duplicates == 0
    assert second.created == 0
    assert second.skipped_duplicates == 5
    with session_factory() as session:
        assert len(session.scalars(select(Document)).all()) == 5
