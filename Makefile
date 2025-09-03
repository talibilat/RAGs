
.PHONY: build run run-local test eval load up-db validate dev-setup clean logs up down

build:
	docker build -t ai-agent .

run:
	docker compose up --build ai-agent

run-local:
	PYTHONPATH=src python -m agent.chat_cli chat

test:
	PYTHONPATH=src pytest -q

eval:
	PYTHONPATH=src python -m agent.eval.ragas_evaluate --examples examples/comprehensive_eval_dataset.json --verbose --output results/ragas_evaluation.json

validate:
	PYTHONPATH=src python -m agent.eval.evaluate --examples examples/validation_set.json

load:
	PYTHONPATH=src python -m agent.data_loader

up-db:
	docker compose up -d postgres

dev-setup: up-db load
	@echo "Development environment ready! Run 'make logs' to see database logs."

clean:
	docker compose down -v
	docker rmi ai-agent 2>/dev/null || true

logs:
	docker compose logs -f postgres

up:
	docker compose up --build

down:
	docker compose down
