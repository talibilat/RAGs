# RAG System with Web Scraper

A comprehensive Retrieval-Augmented Generation (RAG) system with web scraping capabilities for collecting, processing, and retrieving information for question answering.

## 📚 Features

- **Web Scraping**: Automatically crawl and extract content from websites
- **Data Processing**: Transform raw content into structured Q&A pairs
- **Vector Database**: Store embeddings in MongoDB for efficient retrieval
- **RAG Pipeline**: Generate accurate answers based on retrieved context
- **Evaluation System**: Assess the quality of generated responses
- **REST API**: Expose functionalities through a FastAPI backend
- **Frontend Interface**: User-friendly interface for interacting with the system

## 🛠️ System Architecture

The system consists of two main components:

1. **Backend (Python/FastAPI)**: Handles web scraping, data processing, vector storage, and RAG generation
2. **Frontend (Next.js)**: Provides user interface for asking questions and viewing answers

## 🔧 Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB Atlas account (for vector storage)
- Docker and Docker Compose (optional, for containerized deployment)
- API keys for:
  - OpenAI
  - HuggingFace (optional, for alternative embeddings)
  - ScrapFly (for web scraping)
  - FireCrawl (for web crawling)

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# OpenAI API Configuration
OPENAI_API_KEY='your-openai-api-key'
OPENAI_MODEL='gpt-4o'
OPENAI_EMBEDDING_MODEL='text-embedding-ada-002'

# MongoDB Configuration
MONGODB_URI='your-mongodb-connection-string'
MONGODB_DATABASE='manual'
MONGODB_COLLECTION_FAQS='faqs_regex'
MONGODB_VECTOR_INDEX_HF='faqSemanticSearch'
MONGODB_VECTOR_INDEX_OPENAI='faqOpenAISemanticSeachRegex'
MONGODB_VECTOR_NUM_CANDIDATES=100

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# HuggingFace Configuration
HUGGING_FACE_API='your-huggingface-api-key'

# Data Paths
DATA_DIR='data'
PAGES_DIR='data/pages'
FAQS_DIR='data/faqs'
CSV_FILENAME='faqs_regex.csv'

# Web Scraping Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
BASE_URL="https://your-target-website.com"
SCRAPFLY_API_KEY='your-scrapfly-api-key'
FIRECRAWL_API_KEY='your-firecrawl-api-key'
```

### API Keys Setup

1. **OpenAI API Key**: 
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Create an API key in your account dashboard
   - Add to .env file as `OPENAI_API_KEY`

2. **MongoDB Atlas**:
   - Create an account on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Set up a new cluster
   - Create a database user
   - Get your connection string and add to .env as `MONGODB_URI`
   - Set up vector search indexes in your collection

3. **HuggingFace API Key** (optional):
   - Create an account on [HuggingFace](https://huggingface.co/)
   - Generate an API key
   - Add to .env file as `HUGGING_FACE_API`

4. **ScrapFly API Key**:
   - Sign up at [ScrapFly](https://scrapfly.io/)
   - Generate an API key
   - Add to .env file as `SCRAPFLY_API_KEY`

5. **FireCrawl API Key**:
   - Sign up at [FireCrawl](https://firecrawl.dev/)
   - Generate an API key
   - Add to .env file as `FIRECRAWL_API_KEY`

### Installation

#### Method 1: Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd RagWithScraper
```

2. Set up backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up frontend:
```bash
cd ../frontend
npm install
```

#### Method 2: Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd RagWithScraper
```

2. Start the services:
```bash
docker-compose up -d
```

## 🚀 Usage

### Running the System

#### Local Development

1. Start the backend:
```bash
cd backend
python main.py
```

2. Start the frontend:
```bash
cd frontend
npm run dev
```

3. Access the web interface at http://localhost:3000

#### Docker Deployment

```bash
docker-compose up -d
```

Access the web interface at http://localhost:3000

### Web Scraping Pipeline

To scrape a website and process the data:

1. Configure the target website in the `.env` file
2. Run the scraping script:
```bash
cd backend
python -m src.extract_data.fire_crawler
```

3. Process the scraped data:
```bash
python -m src.process_raw_data.extract_faq_from_content
python -m src.process_raw_data.generate_dataset_using_regex
python -m src.process_raw_data.save_faq_to_csv
```

4. Create embeddings and store in MongoDB:
```bash
python -m src.retrieval.create_embeddings
python -m src.retrieval.insert_doc_in_db
```

## 📁 Directory Structure

### Backend

- `backend/`
  - `src/`
    - `evaluation/`: Response evaluation metrics and scoring
    - `extract_data/`: Web scraping and content extraction
    - `generation/`: Answer generation using RAG
    - `process_raw_data/`: Transform raw content into structured data
    - `retrieval/`: Vector search and document retrieval
    - `utils/`: Utility functions for embedding, logging, etc.
  - `main.py`: FastAPI application
  - `requirements.txt`: Python dependencies

### Frontend

- `frontend/`
  - `components/`: React components
  - `pages/`: Next.js pages
  - `public/`: Static assets
  - `styles/`: CSS styles
  - `package.json`: Node.js dependencies

## 🧪 Evaluation

The system includes comprehensive evaluation metrics:

- Semantic similarity scoring
- LLM-based evaluation of factual accuracy, relevance, completeness
- Context relevancy assessment
- Overall confidence scoring

## 📝 License

[Specify your license here]

## 🙏 Acknowledgements

- OpenAI for the language models
- MongoDB for vector storage
- ScrapFly and FireCrawl for web scraping capabilities 