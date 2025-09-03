
# RAG - PyTorch, Pandas, OpenAI, SentenceTransformer

The **RAG** backend is responsible for handling file uploads, processing PDF documents, generating embeddings, and managing user queries based on pre-processed documents. The backend exposes APIs for uploading documents, processing them, and providing answers to user queries.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Contributing](#contributing)
- [License](#license)

## Features

- **PDF Upload**: Allows users to upload PDF documents for processing.
- **Embedding Generation**: Processes the uploaded PDFs, extracts text, and generates embeddings using models.
- **Query Handling**: Users can query the system based on the document contents, and the backend will return relevant responses.
- **CORS Support**: Supports Cross-Origin Resource Sharing (CORS) for frontend-backend communication.

## Installation

### Prerequisites

Make sure you have the following installed on your machine:
- **Python 3.8+**
- **pip** (Python package installer)
- **Virtual environment** (optional, but recommended)

### Step 1: Clone the repository
Clone the repository from GitHub:

```bash
git clone https://github.com/yourusername/localrag-backend.git
cd localrag-backend
```

### Step 2: Set up a virtual environment (optional, but recommended)

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### Step 3: Install dependencies
Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Step 4: Configuration
- Ensure that you have a `config.yaml` file in the root directory that contains the necessary configurations such as API keys and model paths.
- Example of `config.yaml`:

```yaml
chunk_size: 500
embedding_model: "all-MiniLM-L6-v2"
```

### Step 5: Run the FastAPI server
You can start the FastAPI development server with the following command:

```bash
uvicorn main:app --reload
```

The API will now be accessible at `http://127.0.0.1:8000`.

## Usage

Once the server is running, you can use the following steps:
1. **Upload a PDF**: Use the `/upload/` endpoint to upload a PDF. The backend will process the document and create embeddings.
2. **Submit Queries**: Use the `/chatbot/` endpoint to ask questions based on the uploaded document. The system will return relevant answers based on the generated embeddings.

## API Endpoints

### `POST /upload/`
- **Description**: Upload a PDF file to be processed and generate embeddings.
- **Request**: `multipart/form-data` with a PDF file.
- **Response**: Returns the filename and a success message.

**Example Request**:
```bash
curl -X POST "http://127.0.0.1:8000/upload/" -F "file=@yourfile.pdf"
```

**Response**:
```json
{
  "filename": "yourfile.pdf",
  "status": "Embeddings created successfully"
}
```

### `POST /chatbot/`
- **Description**: Submit a query based on pre-saved embeddings from the PDF.
- **Request**: `application/x-www-form-urlencoded` with a query string.
- **Response**: Returns the query and a generated answer.

**Example Request**:
```bash
curl -X POST "http://127.0.0.1:8000/chatbot/" -d "query=What is mentioned in section 4?"
```

**Response**:
```json
{
  "query": "What is mentioned in section 4?",
  "answer": "Section 4 discusses..."
}
```

## Project Structure

```plaintext
Factor-RAG Backend/
│
├── data/                       # Directory for storing uploaded files and embeddings
├── modules/                    # Contains helper modules (PDF processing, embeddings, etc.)
│   ├── main.py                 # Main logic for processing PDFs and handling queries
│   └── utils.py                # Utility functions (e.g., config loading, embeddings)
├── config.yaml                 # Configuration file (contains API keys, model configurations, etc.)
├── main.py                     # Main FastAPI app entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This README file
```

## Technologies

- **FastAPI**: A modern, fast web framework for building APIs with Python.
- **Sentence Transformers**: Used for generating embeddings from document text.
- **OpenAI API**: Used for embedding models (can be replaced with local models if needed).
- **PyTorch**: For handling tensor operations and embeddings.
- **Uvicorn**: ASGI server for running the FastAPI application.

## Contributing

We welcome contributions to improve the project! Here’s how you can contribute:

1. Fork the repository.
2. Create a new feature branch: `git checkout -b feature-branch-name`.
3. Commit your changes: `git commit -m 'Add new feature'`.
4. Push the branch: `git push origin feature-branch-name`.
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

### How to use it:
- Just copy and paste this markdown text into a `README.md` file for the backend project.
- You can replace placeholders like `yourusername` with your actual GitHub username or any other relevant info.

This README provides a comprehensive overview of how to set up, run, and use the backend. If you need additional sections or changes, feel free to ask!