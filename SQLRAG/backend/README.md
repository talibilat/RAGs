# SQLRAG - SQL-based RAG Agent for Financial Data Analysis

A sophisticated Retrieval-Augmented Generation (RAG) system that converts natural language queries into SQL and provides intelligent financial data analysis.

## 🏗️ Architecture

This project implements a **modular architecture** with clear separation of concerns:

- **Core Module** (`src/core/`): Database, configuration, monitoring, and utilities
- **Agent Module** (`src/agent/`): Chat interface, SQL generation, and data loading
- **Evaluation Module** (`src/eval/`): RAGAS evaluation framework and testing
- **Natural Language → SQL → Answer Pipeline**
- **PostgreSQL Integration** with normalized financial data and connection pooling
- **Production-Ready Monitoring** with health checks and graceful shutdown
- **Docker Containerization** with docker-compose
- **Interactive CLI** with Rich formatting

## 🚀 Quick Start

### Prerequisites
- Docker and Python 3.12
- Environment variables (see `env.example`):
  - `DATABASE_HOSTNAME`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`
  - `OPENAI_API_KEY`, `OPENAI_MODEL`

**Important**: You must create a `.env` file from `env.example` before running any commands.

### Setup
```bash
# 1. Copy environment file and set your OpenAI API key
cp env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Set up development environment (starts postgres and loads data)
make setup

# 3. Run evaluation and start interactive chat
make eval
```

### Manual Testing
```bash
# Run tests locally
make test

# Run validation tests
make validate

# Run RAGAS evaluation (followed by interactive chat)
make eval

# Start interactive chat only
make chat

# Start interactive chat in Docker
make run
```

## 📊 Features

### Core Functionality
- **Natural Language to SQL**: Convert questions like "What's the latest revenue for each company?" into SQL queries
- **Financial Data Analysis**: Specialized for financial metrics, cap tables, and company data
- **Interactive Chat Interface**: Rich CLI with Typer framework, syntax highlighting and error handling
- **Health Monitoring**: Built-in health checks for system status and database connectivity
- **Comprehensive Evaluation**: RAGAS metrics for quality assessment with detailed analytics

### Data Pipeline
1. **ETL Process**: JSON financial data → PostgreSQL normalized tables
2. **Schema Management**: Automatic table creation and data loading
3. **Query Optimization**: Intelligent SQL generation with error handling
4. **Result Formatting**: Rich console output with tables and charts

### Production Features
- **Connection Pooling**: Optimized database connections with configurable pool size
- **Health Monitoring**: System health checks for database and configuration
- **Graceful Shutdown**: Proper cleanup of resources on termination
- **Performance Monitoring**: Query performance tracking and slow query detection
- **Error Handling**: Comprehensive error handling with detailed logging
- **Configuration Management**: Environment-based configuration with validation

## 🛠️ Development

### Available Commands
```bash
# Main workflow
make setup        # Set up development environment (postgres + data loading)
make eval         # Run RAGAS evaluation + start interactive chat
make chat         # Start interactive chat only
make run          # Start interactive chat in Docker
make test         # Run test suite locally
make validate     # Run validation tests locally
make clean        # Clean up (removes volumes and images)
```

### Project Structure
```
SQLRAG/
├── src/
│   ├── core/              # Core infrastructure
│   │   ├── config.py      # Configuration management with Pydantic
│   │   ├── database.py    # Database connection pooling and optimization
│   │   ├── models.py      # SQLAlchemy ORM models and Pydantic schemas
│   │   ├── monitoring.py  # Health checks and graceful shutdown
│   │   ├── utils.py       # Utility functions
│   │   └── validation.py  # Data validation
│   ├── agent/             # Agent implementation
│   │   ├── chat_cli.py    # Interactive CLI interface with Typer
│   │   ├── chat_sql.py    # SQL generation and execution
│   │   ├── data_loader.py # ETL and data management
│   │   ├── config.py      # Agent-specific configuration
│   │   └── prompts.py     # LLM prompts and templates
│   └── eval/              # Evaluation framework
│       ├── ragas_evaluate.py    # RAGAS evaluation with comprehensive metrics
│       ├── evaluate.py          # Traditional evaluation methods
│       └── enhanced_evaluate.py # Enhanced evaluation features
├── examples/             # Sample data and test cases
├── docs/                # Documentation
├── tests/               # Test suite
├── results/             # Evaluation results
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Multi-service setup
├── Makefile            # Development commands
├── env.example         # Environment configuration template
└── requirements.txt     # Python dependencies
```

## 🏛️ Modular Architecture

### Core Module (`src/core/`)
- **Configuration Management**: Pydantic-based settings with environment variable support
- **Database Layer**: Connection pooling, health checks, and performance optimization
- **Monitoring**: System health checks, graceful shutdown, and performance metrics
- **Models**: SQLAlchemy ORM models and Pydantic schemas for type safety
- **Utilities**: Common helper functions and SQL sanitization

### Agent Module (`src/agent/`)
- **Chat Interface**: Interactive CLI with Typer framework and Rich formatting
- **SQL Generation**: Natural language to SQL conversion with error handling
- **Data Loading**: ETL pipeline for financial data normalization
- **Prompts**: LLM prompt templates and conversation management

### Evaluation Module (`src/eval/`)
- **RAGAS Integration**: Comprehensive evaluation with multiple metrics
- **Traditional Metrics**: Numeric recall, keyword coverage, and citation analysis
- **Performance Analysis**: Question type, difficulty, and category breakdowns

## 📈 Evaluation

### RAGAS Metrics
- **Faithfulness**: How well the generated SQL matches the intent
- **Answer Relevancy**: Quality of the final answers
- **Context Precision**: Relevance of retrieved context
- **Context Recall**: Completeness of retrieved information
- **Answer Correctness**: Accuracy of generated responses
- **Answer Similarity**: Semantic similarity to ground truth

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
OPENAI_MODEL=gpt-4o-mini

# Application Configuration
LOG_LEVEL=INFO
DATA_PATH=financial_data.json
AGENT_OFFLINE_MODE=false
FEATURE_AGENT_ENABLED=false

# Performance Configuration
DB_MAX_CONNECTIONS=20
DB_CONNECTION_TIMEOUT=30
QUERY_TIMEOUT=60
```

## 📚 Documentation

- **`docs/EVALUATION_FRAMEWORK.md`**: Evaluation methodology and metrics
- **`docs/RAGAS_EVALUATION_SUMMARY.md`**: Performance analysis and results
- **`env.example`**: Environment configuration template

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and evaluation
5. Submit a pull request

## 📄 License

This project is part of the RAGs repository collection.
