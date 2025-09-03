## 9fin SQL Chat Agent

Function-based agent that generates PostgreSQL from natural language, executes it, and answers with inline sources.

### Prerequisites
- Docker and Python 3.12
- Environment variables (see `.env.example`):
  - `DATABASE_HOSTNAME`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`
  - `OPENAI_API_KEY`, `OPENAI_MODEL`

### Quick Start
```bash
# 1. Copy environment file and set your OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Set up development environment (starts postgres and loads data)
make dev-setup

# 3. Start the chat interface
make run
```

### Manual Setup
```bash
# Start Postgres
make up-db

# Install dependencies
pip install -r requirements.txt

# Load sample data into Postgres
make load

# Chat CLI (local development)
PYTHONPATH=src python -m agent.chat_cli chat
```

### What changed vs previous version
- Removed legacy class-based agent; only SQLAlchemy models remain as classes
- Replaced retrieval and formatting with a SQL-first pipeline (`src/agent/chat_sql.py`)

### Tests
Purpose: smoke-check the pipeline and ensure the SQL→answer path works.

Run:
```bash
pytest -q
```
Notes:
- Tests are skipped if DB/OpenAI env vars are not set
- Use `docker compose up -d postgres` and set env to enable

### Evaluation
Purpose: comprehensive quality assessment using RAGAS metrics.

Run:
```bash
make eval
```

### Evaluation and Validation datasets
We include two evaluation sets:

1. **`examples/comprehensive_eval_dataset.json`** - Comprehensive RAGAS evaluation with:
   - Multiple question types (factual lookup, analytical advice, framework analysis)
   - Difficulty levels (easy, medium, hard)
   - Ground truth answers and context
   - Expected numbers and keywords for validation

2. **`examples/validation_set.json`** - Grounded validation with expected numbers:
   - Company count (3)
   - Latest Sales for each company
   - Total cap table amounts
   - Specific leverage and coverage metrics

Run validation:
```bash
make validate
```

### Complete Development Workflow
```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 2. Quick development setup
make dev-setup

# 3. Run tests
make test

# 4. Run comprehensive evaluation
make eval

# 5. Run validation
make validate

# 6. Start chat (Docker)
make run

# 7. Or start chat locally
PYTHONPATH=src python -m agent.chat_cli chat
```

### Docker Commands
```bash
# Run full stack (postgres + ai-agent)
make up

# Run only the AI agent (requires postgres to be running)
make run

# Run locally (without Docker)
make run-local

# View logs
make logs

# Stop services
make down

# Clean up (removes volumes and images)
make clean
```

