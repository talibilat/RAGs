# 9fin SQL Agent - Complete Project Flow Diagram

## 🏗️ **Project Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               9fin SQL Agent                                   │
│                         Function-based AI Agent                                │
│                    Natural Language → SQL → Answer                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📁 **File Structure & Flow**

### **1. Entry Points & Orchestration**

#### **Dockerfile** (Lines 1-35)
```
FROM python:3.12-slim AS base
├── Environment setup (PYTHONDONTWRITEBYTECODE, PYTHONUNBUFFERED)
├── User creation (app user)
├── Dependencies installation (requirements.txt)
├── Source code copy (src/, examples/, financial_data.json)
├── Environment variables setup
└── ENTRYPOINT: python -m agent.chat_cli chat
```

#### **docker-compose.yml** (Lines 1-47)
```
Services:
├── postgres (Lines 3-19)
│   ├── Image: postgres:16
│   ├── Environment: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
│   ├── Ports: 5432:5432
│   ├── Volumes: postgres-db
│   └── Healthcheck: pg_isready
└── ai-agent (Lines 21-41)
    ├── Build: . (uses Dockerfile)
    ├── Depends on: postgres (health check)
    ├── Environment: Database connection vars
    ├── Volumes: financial_data.json
    └── Interactive: stdin_open, tty
```

#### **Makefile** (Lines 1-47)
```
Commands:
├── build: docker build -t ai-agent
├── run: docker compose up --build ai-agent
├── run-local: PYTHONPATH=src python -m agent.chat_cli chat
├── test: PYTHONPATH=src pytest -q
├── eval: RAGAS evaluation with comprehensive dataset
├── validate: Basic validation with expected numbers
├── load: PYTHONPATH=src python -m agent.data_loader
├── up-db: docker compose up -d postgres
├── dev-setup: up-db + load (one-command setup)
├── clean: docker compose down -v + image removal
├── logs: docker compose logs -f postgres
├── up: docker compose up --build (full stack)
└── down: docker compose down
```

### **2. Core Application Flow**

#### **src/agent/chat_cli.py** (Lines 1-52)
```
Entry Point: python -m agent.chat_cli chat
├── main() callback (Lines 16-32)
│   ├── dotenv.load_dotenv()
│   ├── validate_env() - Check required env vars
│   └── validate_db_schema() - Test DB connection
└── chat() command (Lines 34-48)
    ├── Interactive loop: input() → answer_question() → Markdown output
    ├── Handles: exit/quit commands, EOF, empty input
    └── Uses: Rich console for formatted output
```

#### **src/agent/chat_sql.py** (Lines 1-108)
```
Main Pipeline: answer_question(question) → str
├── Environment Setup (Lines 37-55)
│   ├── Database connection: DATABASE_URL
│   ├── LLM setup: ChatOpenAI with structured output
│   └── Schema extraction: db.get_table_info()
├── generate_sql(question, session_id) (Lines 58-68)
│   ├── Uses: sql_query_prompt + structured_llm
│   ├── Returns: sanitized SQL string
│   └── Logs: Generated SQL for debugging
├── run_sql(sql) (Lines 74-84)
│   ├── Executes: db.run(sql)
│   ├── Error handling: Exception logging
│   └── Returns: SQL result string
└── answer_question() (Lines 87-105)
    ├── Chain: question → SQL → execution → answer
    ├── Uses: RunnablePassthrough + rephrase_answer
    └── Returns: Natural language answer with citations
```

### **3. Data Layer**

#### **src/agent/models.py** (Lines 1-95)
```
SQLAlchemy Models:
├── CompanyFinancials (Lines 36-46)
│   ├── Raw JSON storage per company
│   ├── Fields: company_id, company, currency, periods, key_financials, cash_flow_and_leverage, cap_table
│   └── Purpose: Source of truth for company data
├── FinancialMetricsNormalized (Lines 49-72)
│   ├── Flattened time-series metrics
│   ├── Fields: company_id, metric_name, category, unit, period_date, period_type, value, source_url
│   ├── Unique constraint: company_id + metric_name + period_date + period_type + category
│   └── Purpose: Queryable fact table for metrics
├── CapTableNormalized (Lines 75-92)
│   ├── Capital structure normalization
│   ├── Fields: company_id, instrument_name, note, security, maturity_date, rate, amount_usdm, x_ebitda, percent_cap, is_subtotal, as_of_date, source_url
│   └── Purpose: Queryable fact table for capital structure
└── SQLQuery (Lines 94-95)
    ├── Pydantic model for structured LLM output
    └── Field: sql (PostgreSQL query string)
```

#### **src/agent/data_loader.py** (Lines 1-164)
```
ETL Pipeline: financial_data.json → PostgreSQL
├── get_engine() (Lines 30-32)
│   └── Creates SQLAlchemy engine from DATABASE_URL
├── create_schema(engine) (Lines 35-39)
│   ├── Creates pgcrypto extension
│   └── Creates all ORM tables
├── load_json(path) (Lines 42-45)
│   └── Reads and parses JSON file
├── upsert_company_financials(session, company_record) (Lines 48-76)
│   ├── Inserts or updates raw JSON documents
│   ├── Handles: Existing company updates
│   └── Stores: Complete company financial data
├── normalize_metrics(session, company_record) (Lines 78-111)
│   ├── Flattens key_financials and cash_flow_and_leverage
│   ├── Creates: One row per metric per period
│   └── Handles: Multiple periods and categories
├── normalize_cap_table(session, company_record) (Lines 114-143)
│   ├── Flattens cap_table structure
│   ├── Handles: Maturity date parsing
│   └── Creates: One row per instrument
└── main() (Lines 146-163)
    ├── Orchestrates: create_schema → load_json → process each company
    ├── Processes: upsert_company_financials → normalize_metrics → normalize_cap_table
    └── Commits: All changes to database
```

### **4. AI & Prompting**

#### **src/agent/prompts.py** (Lines 1-135)
```
LangChain Prompts:
├── sql_query_prompt (Lines 6-46)
│   ├── System message: PostgreSQL expert instructions
│   ├── Requirements: Source URL handling, unit columns, aggregate functions
│   ├── Schema injection: {schema} placeholder
│   ├── Question injection: {question} placeholder
│   └── Chat history: MessagesPlaceholder for context
└── generation_answer_prompt (Lines 49-134)
    ├── System message: Answer generation with citations
    ├── Few-shot examples: 3 examples with proper citation format
    ├── Input: {question}, {query}, {result}
    └── Output: Natural language answer with [1][2][3] citations
```

#### **src/agent/utils.py** (Lines 1-23)
```
Utility Functions:
└── sanitize_sql(sql_text) (Lines 5-20)
    ├── Removes: Markdown fences (```)
    ├── Removes: Leading 'sql' tags
    └── Returns: Clean SQL string for execution
```

### **5. Validation & Environment**

#### **src/agent/validation.py** (Lines 1-28)
```
Validation Functions:
├── validate_env(required_vars) (Lines 8-12)
│   ├── Checks: Environment variables exist
│   └── Raises: RuntimeError for missing vars
└── validate_db_schema() (Lines 15-27)
    ├── Creates: Database connection
    ├── Tests: Basic connectivity (SELECT 1)
    └── Purpose: Fail fast on misconfiguration
```

### **6. Evaluation Framework**

#### **src/agent/eval/ragas_evaluate.py** (Lines 1-417)
```
RAGAS Evaluation Pipeline:
├── RAGASEvaluationResult (Lines 27-38)
│   └── Dataclass: question, context, ground_truth, generated_answer, metrics
├── extract_numbers(text) (Lines 41-43)
│   └── Regex: Extracts numeric values from text
├── extract_keywords(text) (Lines 46-50)
│   ├── Regex: Extracts words, filters stop words
│   └── Returns: Clean keyword list
├── calculate_traditional_metrics() (Lines 53-81)
│   ├── Numeric recall: Expected vs actual numbers
│   ├── Keyword coverage: Expected vs found keywords
│   ├── Citation analysis: Count and presence
│   └── Answer length: Character count
├── prepare_ragas_dataset() (Lines 84-110)
│   ├── Calls: answer_question() for each test case
│   ├── Handles: Errors gracefully
│   └── Returns: DataFrame in RAGAS format
├── run_ragas_evaluation() (Lines 113-140)
│   ├── Metrics: faithfulness, answer_relevancy, context_relevance, context_recall, answer_correctness, answer_similarity
│   ├── Evaluates: Generated answers vs ground truth
│   └── Returns: RAGAS metrics scores
├── run_traditional_evaluation() (Lines 143-170)
│   ├── Calculates: Traditional metrics for each question
│   └── Returns: Aggregated traditional metrics
└── main() (Lines 173-417)
    ├── Argument parsing: --examples, --verbose, --output
    ├── Loads: Evaluation dataset from JSON
    ├── Runs: RAGAS + traditional evaluation
    ├── Outputs: Results to console and JSON file
    └── Handles: Error cases and logging
```

## 🔄 **Complete Data Flow**

### **1. Setup Phase**
```
.env.example → .env (user configures)
├── make dev-setup
│   ├── make up-db (starts postgres)
│   └── make load (runs data_loader.py)
│       ├── financial_data.json → PostgreSQL
│       ├── Raw JSON → company_financials table
│       ├── Normalized metrics → financial_metrics_normalized table
│       └── Normalized cap table → cap_table_normalized table
```

### **2. Runtime Phase**
```
User Input → chat_cli.py
├── validate_env() → Check environment variables
├── validate_db_schema() → Test database connection
└── Interactive Loop:
    ├── input() → User question
    ├── answer_question() → chat_sql.py
    │   ├── generate_sql() → LLM generates SQL
    │   │   ├── sql_query_prompt + schema → structured_llm
    │   │   └── sanitize_sql() → Clean SQL string
    │   ├── run_sql() → Execute against PostgreSQL
    │   └── rephrase_answer → LLM generates answer
    │       ├── generation_answer_prompt + question + query + result
    │       └── Natural language answer with citations
    └── Markdown output → Rich console
```

### **3. Evaluation Phase**
```
make eval → ragas_evaluate.py
├── Load comprehensive_eval_dataset.json
├── For each question:
│   ├── answer_question() → Generate answer
│   ├── calculate_traditional_metrics() → Basic metrics
│   └── prepare_ragas_dataset() → RAGAS format
├── run_ragas_evaluation() → Advanced metrics
├── run_traditional_evaluation() → Basic metrics
└── Output: results/ragas_evaluation.json
```

## 🎯 **Key Design Patterns**

### **1. Function-Based Architecture**
- No classes except SQLAlchemy models and Pydantic schemas
- Pure functions for business logic
- Easy testing and composition

### **2. Pipeline Pattern**
- Clear separation: question → SQL → execution → answer
- LangChain runnables for chaining operations
- Error handling at each stage

### **3. ETL Pattern**
- Extract: JSON files
- Transform: Normalize nested structures
- Load: PostgreSQL tables

### **4. Validation Pattern**
- Environment validation at startup
- Database connectivity checks
- Graceful error handling

### **5. Evaluation Pattern**
- Multiple evaluation approaches (traditional + RAGAS)
- Comprehensive metrics
- Structured output for analysis

## 🔧 **Configuration Flow**

```
Environment Variables:
├── Database: DATABASE_HOSTNAME, DATABASE_PORT, DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD
├── OpenAI: OPENAI_API_KEY, OPENAI_MODEL
├── Agent: AGENT_OFFLINE_MODE, FEATURE_AGENT_ENABLED
└── Data: DATA_PATH

Configuration Sources:
├── .env file (user-configured)
├── Environment variables (system)
├── Default values (fallback)
└── Docker environment (container)
```

## 📊 **Database Schema**

```
PostgreSQL Database:
├── company_financials (Raw JSON storage)
│   ├── company_id (PK)
│   ├── company, currency
│   └── periods, key_financials, cash_flow_and_leverage, cap_table (JSON)
├── financial_metrics_normalized (Fact table)
│   ├── id (PK)
│   ├── company_id, metric_name, category, unit
│   ├── period_date, period_type, value
│   └── source_url
└── cap_table_normalized (Fact table)
    ├── id (PK)
    ├── company_id, instrument_name, note, security
    ├── maturity_date, rate, amount_usdm, x_ebitda, percent_cap
    ├── is_subtotal, as_of_date
    └── source_url
```

This architecture provides a robust, scalable, and maintainable system for converting natural language questions into SQL queries and generating comprehensive answers with proper citations.
