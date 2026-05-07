.PHONY: reset up down test step00-qasper evidence-pack latency

reset:
	docker compose down -v --remove-orphans
	rm -f .env.cache
	docker compose up -d --build

up:
	docker compose up -d

down:
	docker compose down

test:
	venv/bin/python -m pytest tests -q

step00-qasper:
	venv/bin/python -m src.datasets.qasper_step00 --root .

latency:
	venv/bin/python -m src.operations.latency --backend fixture --queries 100 --concurrency 25 --output evidence/step08/latency_report.json

evidence-pack:
	venv/bin/python -m src.operations.evidence_pack --repo-root . --output evidence/final
