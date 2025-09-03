# RAG System Backend Architecture

This document provides an overview of the backend architecture for the RAG (Retrieval-Augmented Generation) system with web scraping capabilities.

## Directory Structure

The backend code is organized into the following modules:

### 📋 `evaluation/`

The evaluation module provides comprehensive metrics for assessing the quality of RAG system responses.

- **evaluator.py**: Core evaluation logic for RAG responses, combining multiple metrics into an overall confidence score
- **metrics.py**: Implementation of evaluation metrics including semantic similarity and LLM-based assessment

### 🔍 `extract_data/`

This module contains web scraping and data extraction functionality.

- **fire_crawler.py**: Web crawler using FireCrawl API to extract content from target websites
- **break_data_into_pages.py**: Processes crawled web content into manageable pages for further processing

### 🤖 `generation/`

The generation module implements the RAG pipeline for answer generation.

- **generating_output.py**: Creates and executes the RAG chain for generating answers to user questions

### 📊 `process_raw_data/`

This module processes raw extracted data into structured Q&A pairs for the RAG system.

- **extract_faq_from_content.py**: Extracts FAQ-like content from raw HTML/text
- **generate_dataset_using_regex.py**: Uses regex patterns to identify question-answer pairs
- **save_faq_to_csv.py**: Exports processed FAQs to CSV format
- **instructor_ai.py**: Uses AI to help structure and clean extracted data

### 🗄️ `retrieval/`

The retrieval module handles vector embeddings and similarity search.

- **create_embeddings.py**: Generates vector embeddings for documents
- **insert_doc_in_db.py**: Inserts embedded documents into MongoDB
- **retrieval.py**: Demonstrates retrieval of similar documents (example implementation)

### 🛠️ `utils/`

Common utilities used across the system.

- **logger.py**: Centralized logging configuration
- **mongo_client.py**: MongoDB connection and collection management
- **retriever_client.py**: Vector search client for semantic retrieval
- **hf_embeddings.py**: HuggingFace embedding generation utilities
- **openai_embeddings.py**: OpenAI embedding generation utilities

## Data Flow

1. **Data Extraction Pipeline**:
   - Web scraping using FireCrawl (`extract_data/fire_crawler.py`)
   - Content extraction and page splitting (`extract_data/break_data_into_pages.py`)
   - FAQ extraction and processing (`process_raw_data/` modules)
   
2. **Embedding and Storage**:
   - Embedding generation (`retrieval/create_embeddings.py`)
   - Database storage (`retrieval/insert_doc_in_db.py`)
   
3. **RAG Pipeline**:
   - Question input → Retrieval → Context formation → LLM generation → Response
   - Handled primarily by `generation/generating_output.py`
   
4. **Evaluation Pipeline**:
   - Response assessment using multiple metrics (`evaluation/` modules)
   - Results storage for tracking and improvement

## Integration Points

- **FastAPI Backend**: The modules are integrated into the FastAPI application in `main.py`
- **MongoDB Vector Database**: Document storage and semantic search
- **OpenAI API**: LLM for answer generation and evaluation
- **Scraping APIs**: FireCrawl for web content extraction 