# SQLRAG - SQL-based RAG Agent for Financial Data Analysis

A sophisticated Retrieval-Augmented Generation (RAG) system that converts natural language queries into SQL and provides intelligent financial data analysis.

## 🏗️ Architecture

This project implements a **function-based architecture** with clear separation of concerns:

- **Natural Language → SQL → Answer Pipeline**
- **PostgreSQL Integration** with normalized financial data
- **RAGAS Evaluation Framework** for comprehensive testing
- **Docker Containerization** with docker-compose
- **Interactive CLI** with Rich formatting

## 🚀 Quick Start

### Prerequisites
- Docker and Python 3.12
- Environment variables (see `.env.example`):
  - `DATABASE_HOSTNAME`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`
  - `OPENAI_API_KEY`, `OPENAI_MODEL`

### Setup
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

## 📊 Features

### Core Functionality
- **Natural Language to SQL**: Convert questions like "What's the latest revenue for each company?" into SQL queries
- **Financial Data Analysis**: Specialized for financial metrics, cap tables, and company data
- **Interactive Chat Interface**: Rich CLI with syntax highlighting and error handling
- **Comprehensive Evaluation**: RAGAS metrics for quality assessment

### Data Pipeline
1. **ETL Process**: JSON financial data → PostgreSQL normalized tables
2. **Schema Management**: Automatic table creation and data loading
3. **Query Optimization**: Intelligent SQL generation with error handling
4. **Result Formatting**: Rich console output with tables and charts

## 🛠️ Development

### Available Commands
```bash
# Development workflow
make dev-setup    # Quick setup (postgres + data loading)
make test         # Run test suite
make eval         # Run comprehensive RAGAS evaluation
make validate     # Run validation tests

# Docker commands
make up           # Run full stack (postgres + ai-agent)
make run          # Run only AI agent
make run-local    # Run locally without Docker
make logs         # View logs
make down         # Stop services
make clean        # Clean up (removes volumes and images)
```

### Project Structure
```
SQLRAG/
├── src/agent/           # Core agent implementation
│   ├── chat_cli.py     # Interactive CLI interface
│   ├── chat_sql.py     # SQL generation and execution
│   ├── data_loader.py  # ETL and data management
│   ├── models.py       # Data models and schemas
│   ├── prompts.py      # LLM prompts and templates
│   ├── utils.py        # Utility functions
│   ├── validation.py   # Data validation
│   └── eval/           # Evaluation framework
├── examples/           # Sample data and test cases
├── docs/              # Documentation
├── tests/             # Test suite
├── results/           # Evaluation results
├── Dockerfile         # Container configuration
├── docker-compose.yml # Multi-service setup
├── Makefile          # Development commands
└── requirements.txt   # Python dependencies
```

## 📈 Evaluation

### RAGAS Metrics
- **Faithfulness**: How well the generated SQL matches the intent
- **Answer Relevancy**: Quality of the final answers
- **Context Precision**: Relevance of retrieved context
- **Context Recall**: Completeness of retrieved information

### Test Datasets
- **`comprehensive_eval_dataset.json`**: Multi-difficulty questions with ground truth
- **`validation_set.json`**: Expected numbers and metrics validation

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_NAME=9fin
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=password

# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini

# Agent Configuration
AGENT_OFFLINE_MODE=false
FEATURE_AGENT_ENABLED=false

# Data Configuration
DATA_PATH=financial_data.json
```

## 📚 Documentation

- **`PROJECT_FLOW_DIAGRAM.md`**: Complete system architecture and data flow
- **`docs/EVALUATION_FRAMEWORK.md`**: Evaluation methodology and metrics
- **`docs/RAGAS_EVALUATION_SUMMARY.md`**: Performance analysis and results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and evaluation
5. Submit a pull request

## 📄 License

This project is part of the RAGs repository collection.
