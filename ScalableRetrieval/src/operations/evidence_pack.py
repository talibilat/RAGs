from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


REQUIRED_ARTIFACTS = (
    Path("docker-compose.yml"),
    Path(".env.example"),
    Path("evidence/step00/docker_compose_ps.log"),
    Path("evidence/step00/config_loader.log"),
    Path("evidence/step01/first_ingestion.log"),
    Path("evidence/step01/duplicate_ingestion.log"),
    Path("evidence/step01/postgres_counts.log"),
    Path("evidence/step02/parsed_markdown_sample.md"),
    Path("evidence/step02/parse_status.log"),
    Path("evidence/step08/postgres_ledger_1000_dump.log"),
    Path("evidence/step03/zero_waste_embeddings.log"),
    Path("evidence/step04/worker_sync.log"),
    Path("evidence/step05/retrieval_rerank.log"),
    Path("evidence/step06/structured_prompt_template.txt"),
    Path("evidence/step06/red_team_test.log"),
    Path("evidence/step07/evaluation_report.json"),
    Path("evidence/step08/latency_report.json"),
)


@dataclass(frozen=True)
class EvidenceManifest:
    output_dir: Path
    included_artifacts: tuple[str, ...]
    missing_artifacts: tuple[str, ...]


def compile_evidence_pack(repo_root: Path, output_dir: Path) -> EvidenceManifest:
    repo_root = Path(repo_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    included: list[str] = []
    missing: list[str] = []

    for artifact in REQUIRED_ARTIFACTS:
        source = repo_root / artifact
        manifest_name = _manifest_name(artifact)
        if not source.exists():
            missing.append(manifest_name)
            continue

        destination = output_dir / manifest_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        included.append(manifest_name)

    manifest = EvidenceManifest(
        output_dir=output_dir,
        included_artifacts=tuple(included),
        missing_artifacts=tuple(missing),
    )
    _write_manifest(manifest, output_dir / "manifest.json")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile final Step 08 evidence pack.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("evidence/final"))
    args = parser.parse_args()

    manifest = compile_evidence_pack(args.repo_root, args.output)
    print(
        "complete={complete} included={included} missing={missing}".format(
            complete=not manifest.missing_artifacts,
            included=len(manifest.included_artifacts),
            missing=len(manifest.missing_artifacts),
        )
    )


def _manifest_name(path: Path) -> str:
    if path.parts[:1] == ("evidence",):
        return str(Path(*path.parts[1:]))
    return path.name


def _write_manifest(manifest: EvidenceManifest, path: Path) -> None:
    payload = {
        "complete": not manifest.missing_artifacts,
        "output_dir": str(manifest.output_dir),
        "included_artifacts": list(manifest.included_artifacts),
        "missing_artifacts": list(manifest.missing_artifacts),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
