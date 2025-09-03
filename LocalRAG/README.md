# LocalRAG - Document Processing and Query System

Factor-RAG is a full-stack application that allows users to upload PDF documents, generate embeddings from the text, and query the document using natural language questions. The backend processes the PDF files and generates embeddings using a model, and the frontend provides an interactive interface for users to upload files and query the document.

## 🏗️ Architecture

This project implements a **document-based RAG system** with:

- **PDF Upload & Processing**: Extract text and generate embeddings
- **Embeddings-Based Search**: Efficient similarity search through document content
- **Frontend & Backend Integration**: React frontend with FastAPI backend
- **Natural Language Querying**: Ask questions about uploaded documents

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (for backend)
- **Node.js** (for frontend)
- **OpenAI API Key**

### Installation

1. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   export OPENAI_API_KEY=your-secret-key
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start Backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   Backend runs at `http://127.0.0.1:8000`

2. **Start Frontend**:
   ```bash
   cd frontend
   npm start
   ```
   Frontend runs at `http://localhost:3000`

## 📁 Project Structure

```
LocalRAG/
├── backend/                # FastAPI backend
│   ├── data/               # PDF storage and embeddings
│   ├── modules/            # Core processing logic
│   │   ├── main.py         # PDF processing and embeddings
│   │   ├── utils.py        # Utility functions
│   │   ├── pdf_processing.py  # PDF text extraction
│   │   └── embedding.py    # Embedding generation
│   ├── config.yaml         # Configuration settings
│   ├── main.py             # FastAPI app entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/                # React source files
│   │   ├── components/     # UI components
│   │   │   ├── FileUpload.js
│   │   │   ├── ChatBox.js
│   │   │   ├── UserImage.js
│   │   │   ├── LoadingBar.js
│   │   │   └── Logo.js
│   │   ├── App.js          # Main React component
│   │   ├── index.js        # React entry point
│   │   └── styles/         # CSS styling
│   ├── public/             # Static assets
│   └── package.json        # npm dependencies
├── docker-compose.yaml     # Docker configuration
├── package.json            # Root package configuration
└── README.md               # This file
```

## 🔧 Configuration

Edit `backend/config.yaml`:
```yaml
model: 'gpt-4o'
chunk_size: 5
top_k: 3
```

- **model**: AI model for embedding and querying
- **chunk_size**: Text chunk size for processing
- **top_k**: Number of top results to return

## 🎯 Features

- **PDF Upload**: Process PDF files for text extraction
- **Query Interface**: Natural language questions about documents
- **Embeddings-Based Search**: Efficient similarity search
- **Real-time Processing**: Live document processing and querying
- **Modern UI**: React-based interactive interface

## 🛠️ Technologies

- **FastAPI**: Backend framework
- **React**: Frontend framework
- **OpenAI GPT-4**: Embeddings and answer generation
- **Sentence Transformers**: Embedding models
- **Axios**: API communication
- **PyTorch**: Tensor operations

---

This project is part of the RAGs repository collection.
