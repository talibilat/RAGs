.PHONY: install dev test fmt eval help

help:
	@echo "Available commands:"
	@echo "  make install   - Install backend and frontend dependencies"
	@echo "  make dev       - Run backend and frontend in dev mode"
	@echo "  make test      - Run tests"
	@echo "  make fmt       - Format code"
	@echo "  make eval      - Run evals"

install:
	@echo "Installing Backend..."
	cd backend && pip install -e .
	@echo "Installing Frontend..."
	cd frontend && npm install

dev: clean-dev
	@echo "Starting Dev Servers..."
	# Basic parallel run. Use specific tools like concurrently or make -j in real usage
	(trap 'kill 0' SIGINT; cd backend && PYTHONPATH=. uvicorn app.main:app --reload --port 8000 --reload-exclude "venv/*" --reload-exclude "*.pyc" --reload-exclude "__pycache__/*" & cd frontend && npm run dev)

clean-dev:
	@echo "Cleaning up existing processes..."
	-@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	-@pkill -f "next dev" 2>/dev/null || true
	-@lsof -ti :8000 | xargs kill -9 2>/dev/null || true
	-@lsof -ti :3000 | xargs kill -9 2>/dev/null || true
	-@rm -f frontend/.next/dev/lock 2>/dev/null || true
	@sleep 1

test:
	cd backend && pytest
	cd frontend && npm test

fmt:
	cd backend && black .
	cd frontend && npm run fmt

eval:
	cd backend && python app/evals/runner.py
