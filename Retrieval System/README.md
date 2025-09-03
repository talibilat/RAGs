# RAGs - Retrieval-Augmented Generation Projects

A comprehensive collection of advanced RAG (Retrieval-Augmented Generation) implementations showcasing different approaches, architectures, and use cases for building intelligent document processing and query systems.

## 🏗️ Project Overview

This repository contains four distinct RAG implementations, each demonstrating different techniques and use cases:

- **SQLRAG**: SQL-based RAG for structured data analysis
- **LocalRAG**: Document processing with local embeddings
- **RagWithScraper**: Web scraping combined with RAG
- **Retrieval System**: Advanced retrieval framework

## 📁 Projects

### 🗄️ [SQLRAG](./SQLRAG/) - SQL-based RAG Agent for Financial Data Analysis
Function-based agent that generates PostgreSQL from natural language, executes it, and answers with inline sources. Specialized for financial data analysis with comprehensive evaluation framework.

**Key Features:**
- Natural Language → SQL → Answer Pipeline
- PostgreSQL Integration with normalized financial data
- RAGAS Evaluation Framework
- Docker Containerization
- Interactive CLI with Rich formatting

**Technologies:** Python, PostgreSQL, OpenAI, LangChain, RAGAS, Docker

### 📚 [LocalRAG](./LocalRAG/) - Document Processing and Query System
Full-stack application for uploading PDF documents, generating embeddings, and querying documents using natural language.

**Key Features:**
- PDF Upload and Text Extraction
- Embeddings-Based Search
- React Frontend with FastAPI Backend
- Real-time Document Processing
- Interactive Chat Interface

**Technologies:** Python, FastAPI, React, OpenAI, Sentence Transformers, Docker

### 🌐 [RagWithScraper](./RagWithScraper/) - Web Scraper RAG
RAG system that combines web scraping with retrieval capabilities to answer questions based on scraped web content.

**Key Features:**
- Multi-source Web Scraping
- Content Preprocessing and Normalization
- Vector Search and Similarity Matching
- Real-time Querying
- Source Attribution and Citation

**Technologies:** Python, BeautifulSoup/Scrapy, OpenAI, Vector Databases, FastAPI

### 🔍 [Retrieval System](./Retrieval%20System/) - Advanced Document Retrieval Framework
Comprehensive retrieval system for efficient document search, similarity matching, and content discovery.

**Key Features:**
- Multi-modal Retrieval (text, images, structured data)
- Advanced Indexing Strategies
- Hybrid Search (semantic + keyword)
- Scalable Architecture
- Performance Benchmarks

**Technologies:** Python, Elasticsearch, FAISS, Transformers, Redis, PostgreSQL

## 🚀 Quick Start

Each project has its own setup instructions. Navigate to the specific project folder for detailed documentation.

### General Prerequisites
- **Python 3.8+** (for most projects)
- **Docker** (for containerized deployments)
- **OpenAI API Key** (for most projects)
- **PostgreSQL** (for SQLRAG)
- **Node.js** (for LocalRAG frontend)

### Environment Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/talibilat/RAGs.git
   cd RAGs
   ```

2. Set up environment variables:
   ```bash
   # Copy example environment file
   cp SQLRAG/.env.example .env
   
   # Edit .env and add your API keys
   nano .env
   ```

3. Choose a project and follow its specific setup instructions.

## 📊 Project Comparison

| Project | Data Source | Embeddings | Search Type | Use Case |
|---------|-------------|------------|-------------|----------|
| **SQLRAG** | Structured (PostgreSQL) | OpenAI | SQL Generation | Financial Analysis |
| **LocalRAG** | Documents (PDF) | OpenAI/Sentence Transformers | Semantic Search | Document Q&A |
| **RagWithScraper** | Web Content | OpenAI | Vector Search | Web Research |
| **Retrieval System** | Multi-modal | Multiple Models | Hybrid Search | Enterprise Search |

## 🛠️ Common Technologies

### Core Technologies
- **Python 3.8+**: Primary programming language
- **OpenAI API**: Embedding generation and text completion
- **LangChain**: LLM application framework
- **Docker**: Containerization
- **FastAPI**: API framework

### Vector Databases
- **FAISS**: Vector similarity search
- **Elasticsearch**: Distributed search engine
- **PostgreSQL**: Relational database with vector extensions

### Frontend Technologies
- **React**: Frontend framework
- **Rich**: Terminal formatting
- **Streamlit**: Rapid prototyping

## 📈 Evaluation and Testing

Each project includes comprehensive evaluation frameworks:

- **RAGAS**: RAG evaluation metrics
- **Custom Metrics**: Domain-specific evaluation
- **Benchmarking**: Performance comparisons
- **A/B Testing**: Model comparison

## 🔧 Development

### Project Structure
```
RAGs/
├── SQLRAG/              # SQL-based RAG implementation
├── LocalRAG/            # Document processing RAG
├── RagWithScraper/      # Web scraping RAG
├── Retrieval System/    # Advanced retrieval framework
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -m 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Include docstrings for functions and classes
- Write tests for new functionality

## 📚 Documentation

Each project contains detailed documentation:
- **Setup Instructions**: Step-by-step installation
- **API Documentation**: Endpoint specifications
- **Architecture Diagrams**: System design
- **Examples**: Usage examples and tutorials

## 🎯 Use Cases

### SQLRAG
- Financial data analysis
- Business intelligence
- Data exploration
- Report generation

### LocalRAG
- Document Q&A
- Knowledge base search
- Research assistance
- Content analysis

### RagWithScraper
- Web research
- Content monitoring
- Competitive intelligence
- News analysis

### Retrieval System
- Enterprise search
- Academic research
- E-commerce search
- Customer support

## 🔒 Security

- API keys are stored in environment variables
- No sensitive data is committed to the repository
- Docker containers run with minimal privileges
- Input validation and sanitization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the project-specific documentation
- Review the examples and tutorials

## 🙏 Acknowledgments

- OpenAI for providing the GPT models
- LangChain for the application framework
- The open-source community for various libraries and tools

---

**Note**: This repository is actively maintained and updated. Check individual project READMEs for the most current information.