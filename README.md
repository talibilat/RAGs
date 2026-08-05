# 🚀 RAGs - Retrieval-Augmented Generation Projects

A comprehensive collection of advanced RAG (Retrieval-Augmented Generation) implementations showcasing different approaches, architectures, and use cases. This repository contains multiple production-ready RAG systems, each designed for specific scenarios and demonstrating various techniques in the RAG ecosystem

## 📋 Table of Contents

- [Overview](#overview)
- [Projects](#projects)
- [Quick Start](#quick-start)
- [Architecture Comparison](#architecture-comparison)
- [Features Matrix](#features-matrix)
- [Installation & Setup](#installation--setup)
- [Usage Examples](#usage-examples)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This repository contains four distinct RAG implementations, each optimized for different use cases:

1. **LocalRAG** - Document processing and query system with React frontend
2. **RagWithScraper** - Web scraping RAG with real-time content processing
3. **SQLRAG** - SQL-based RAG agent for financial data analysis
4. **Retrieval System** - Advanced document retrieval framework with multi-modal support

## 📁 Projects

### 🗄️ SQLRAG - SQL-based RAG Agent for Financial Data Analysis

**Purpose**: Function-based agent that generates PostgreSQL queries from natural language, executes them, and provides answers with inline sources. Specialized for financial data analysis with comprehensive evaluation framework.

**Key Features:**
- 🧠 Natural Language → SQL → Answer Pipeline
- 🐘 PostgreSQL Integration with normalized financial data
- 📊 RAGAS Evaluation Framework
- 🐳 Docker Containerization
- 💬 Interactive CLI with Rich formatting
- ✅ Comprehensive testing and validation

**Tech Stack:**
- Python 3.12, SQLAlchemy, PostgreSQL
- OpenAI GPT models, RAGAS evaluation
- Docker, Makefile automation

**Use Cases:**
- Financial data analysis and reporting
- Business intelligence queries
- Data-driven decision making

---

### 🌐 RagWithScraper - Web Scraper RAG

**Purpose**: RAG system that combines web scraping with retrieval capabilities to answer questions based on scraped web content. Perfect for real-time information gathering and analysis.

**Key Features:**
- 🕷️ Multi-source Web Scraping
- 🔄 Content Preprocessing and Normalization
- 🔍 Vector Search and Similarity Matching
- ⚡ Real-time Querying
- 📚 Source Attribution and Citation
- 📈 Performance Evaluation and Metrics

**Tech Stack:**
- Python 3.12, FastAPI, Next.js
- MongoDB, Vector embeddings
- Web scraping tools, Docker

**Use Cases:**
- Real-time web content analysis
- FAQ generation from websites
- Content monitoring and analysis
- Research automation

---

### 📚 LocalRAG - Document Processing and Query System

**Purpose**: Full-stack application for uploading PDF documents, generating embeddings, and querying documents using natural language. Ideal for document management and knowledge extraction.

**Key Features:**
- 📄 PDF Upload and Text Extraction
- 🧮 Embeddings-Based Search
- ⚛️ React Frontend with FastAPI Backend
- 🔄 Real-time Document Processing
- 💬 Interactive Chat Interface
- 🎨 Modern UI/UX Design

**Tech Stack:**
- Python 3.12, FastAPI, React.js
- Vector databases, PDF processing
- Docker, Modern web technologies

**Use Cases:**
- Document management systems
- Knowledge base creation
- Research and academic applications
- Corporate document analysis

---

### 🔍 Retrieval System - Advanced Document Retrieval Framework

**Purpose**: Comprehensive retrieval system for efficient document search, similarity matching, and content discovery. Demonstrates advanced retrieval techniques and multi-modal capabilities.

**Key Features:**
- 🎭 Multi-modal Retrieval (text, images, structured data)
- 🏗️ Advanced Indexing Strategies
- 🔀 Hybrid Search (semantic + keyword)
- 📈 Scalable Architecture
- 📊 Performance Benchmarks
- 🔬 Research and experimentation tools

**Tech Stack:**
- Python, Jupyter Notebooks
- Azure AI Search, Vector embeddings
- Advanced ML libraries

**Use Cases:**
- Research and development
- Advanced search applications
- Multi-modal content discovery
- Performance benchmarking

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.12+**
- **Node.js 18+** (for frontend projects)
- **OpenAI API Key** (for most projects)
- **PostgreSQL** (for SQLRAG)

### General Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/talibilat/RAGs.git
   cd RAGs
   ```

2. **Choose your project** and navigate to its directory

3. **Follow project-specific setup instructions** in each project's README

## 🏗️ Architecture Comparison

| Project | Backend | Frontend | Database | Vector Store | Specialization |
|---------|---------|----------|----------|--------------|----------------|
| **LocalRAG** | FastAPI | React | SQLite | Embeddings | Document Processing |
| **RagWithScraper** | FastAPI | Next.js | MongoDB | Vector DB | Web Scraping |
| **SQLRAG** | Python CLI | N/A | PostgreSQL | N/A | SQL Generation |
| **Retrieval System** | Jupyter | N/A | Various | Multiple | Research & Analysis |

## 📊 Features Matrix

| Feature | LocalRAG | RagWithScraper | SQLRAG | Retrieval System |
|---------|----------|----------------|--------|------------------|
| **Web Interface** | ✅ React | ✅ Next.js | ❌ CLI Only | ❌ Notebooks |
| **PDF Processing** | ✅ | ❌ | ❌ | ✅ |
| **Web Scraping** | ❌ | ✅ | ❌ | ❌ |
| **SQL Generation** | ❌ | ❌ | ✅ | ❌ |
| **Real-time Processing** | ✅ | ✅ | ✅ | ❌ |
| **Docker Support** | ✅ | ✅ | ✅ | ❌ |
| **Evaluation Framework** | ❌ | ✅ | ✅ | ✅ |
| **Multi-modal** | ❌ | ❌ | ❌ | ✅ |

## 🛠️ Installation & Setup

### SQLRAG Setup
```bash
cd SQLRAG
cp .env.example .env
# Edit .env with your API keys
make dev-setup
make run
```

### LocalRAG Setup
```bash
cd LocalRAG
docker-compose up -d
# Access at http://localhost:3000
```

### RagWithScraper Setup
```bash
cd RagWithScraper
docker-compose up -d
# Access at http://localhost:3000
```

### Retrieval System Setup
```bash
cd "Retrieval System"
# Install Jupyter and dependencies
pip install -r requirements.txt
jupyter notebook
```

## 💡 Usage Examples

### SQLRAG - Financial Analysis
```bash
# Start the chat interface
make run

# Example queries:
# "What are the total sales for each company?"
# "Show me the leverage ratios for all companies"
# "Which company has the highest revenue growth?"
```

### LocalRAG - Document Query
```bash
# Upload PDF documents through the web interface
# Ask questions like:
# "What are the main findings in this document?"
# "Summarize the key points from chapter 3"
```

### RagWithScraper - Web Content Analysis
```bash
# Scrape websites and ask questions:
# "What are the main features of this product?"
# "Extract all FAQ items from this page"
```

## 🔧 Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific project tests
cd SQLRAG && pytest
cd LocalRAG/backend && pytest
```

### Code Quality
```bash
# Lint Python files
flake8 --max-line-length=100

# Format code
black --line-length=100

# Type checking
mypy .
```

## 📈 Performance & Evaluation

- **SQLRAG**: RAGAS evaluation framework with comprehensive metrics
- **RagWithScraper**: Custom evaluation with timing and accuracy metrics
- **LocalRAG**: Real-time performance monitoring
- **Retrieval System**: Benchmark comparisons and research metrics

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models and embeddings
- The RAG research community
- Contributors and users of this project

## 📞 Support

- 📧 Email: [your-email@example.com]
- 🐛 Issues: [GitHub Issues](https://github.com/talibilat/RAGs/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/talibilat/RAGs/discussions)

---

**⭐ If you find this project helpful, please give it a star!**
