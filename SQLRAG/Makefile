
.PHONY: test eval validate setup clean run

# Main commands for automated testing and evaluation
test:
	PYTHONPATH=src pytest -q

eval:
	PYTHONPATH=src python -m eval.ragas_evaluate --examples examples/comprehensive_eval_dataset.json --verbose --output results/ragas_evaluation.json

validate:
	PYTHONPATH=src python -m eval.evaluate --examples examples/validation_set.json

# Setup and run commands
setup:
	@echo "Setting up development environment..."
	docker compose up -d postgres
	@echo "Waiting for database to be ready..."
	@until docker exec postgres pg_isready -U postgres -d 9fin; do \
		echo "Database not ready yet, waiting..."; \
		sleep 2; \
	done
	@echo "Loading sample data..."
	PYTHONPATH=src python -m agent.data_loader
	@echo "Setup complete!"

run:
	@echo "Running automated evaluation..."
	docker compose build --no-cache ai-agent
	@echo "Starting interactive chat..."
	PYTHONPATH=src python -m agent.chat_cli chat
	

# Cleanup
clean:
	docker compose down -v
	docker rmi ai-agent 2>/dev/null || true
