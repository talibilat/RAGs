Based on your inputs, here’s a **README** file that explains the whole project (frontend and backend), how to run the app, and includes the configuration settings.

---

# RAG: Document Processing and Query System

Factor-RAG is a full-stack application that allows users to upload PDF documents, generate embeddings from the text, and query the document using natural language questions. The backend processes the PDF files and generates embeddings using a model, and the frontend provides an interactive interface for users to upload files and query the document.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)

## Overview

The **Factor-RAG** system works by allowing users to upload PDF documents to the backend, which processes the files to extract text and generate embeddings. These embeddings are then used to answer user queries about the document. The frontend provides a user-friendly interface to upload files, ask questions, and display AI-generated answers.

## Features

- **PDF Upload**: Users can upload PDF files which are processed for text and embeddings.
- **Query Interface**: Users can ask questions about the content of the uploaded document and receive AI-generated answers.
- **Embeddings-Based Search**: The backend processes the text into embeddings and efficiently searches through these embeddings to provide relevant answers.
- **Frontend & Backend Integration**: The frontend communicates with the backend via RESTful APIs.

## Installation

### Prerequisites

Ensure you have the following installed:
- **Python 3.8+** (for backend)
- **Node.js** (for frontend)
- **pip** (Python package manager)
- **npm** (Node.js package manager)

### Step 1: Clone the repository

```bash
git clone https://github.com/talibilat/rags.git
cd rags
```

### Step 2: Install Backend Dependencies

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Export your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your-secret-key
   ```

### Step 3: Install Frontend Dependencies

1. Navigate to the `frontend/` directory:
   ```bash
   cd ../frontend
   ```

2. Install the Node.js dependencies:
   ```bash
   npm install
   ```

## Configuration

The backend uses a configuration file (`config.yaml`) where you can set parameters for the model, chunk size, and the number of top results to return for each query.

Example of `backend/config.yaml`:
```yaml
model: 'gpt-4o'
chunk_size: 5
top_k: 3
```

- **model**: The AI model to use for embedding and querying (e.g., GPT-4).
- **chunk_size**: The size of the chunks into which the PDF text is divided.
- **top_k**: Number of top results to return for each query.

Make sure the **`OPENAI_API_KEY`** is exported in your environment before running the backend.

## Running the Application

### Running the Backend

1. After configuring the backend and installing dependencies, start the FastAPI backend by running the following in the `backend/` directory:
   
   
   ```bash
   cd backend
   ```

   ```bash
   uvicorn main:app --reload
   ```

   This will start the backend server at `http://127.0.0.1:8000`.

### Running the Frontend

1. In a new terminal window or tab, navigate to the `frontend/` directory:

   ```bash
   cd frontend
   ```

2. Start the React development server:

   ```bash
   npm start
   ```

   The frontend will start running on `http://localhost:3000`.

### Full Workflow

1. **Upload a PDF**: Navigate to the frontend (`http://localhost:3000`) and use the "Upload New File" button to upload a PDF document. Once uploaded, the backend will process the document and generate embeddings.
   
2. **Ask Questions**: After the PDF is processed, you can type questions in the query input box and press "Send". The system will use the embeddings to find relevant answers from the uploaded document and display them in the chatbox.

## Project Structure

```plaintext
factor-rag/
│
├── backend/                # Backend folder (FastAPI-based)
│   ├── data/               # Directory for storing uploaded PDFs and embeddings
│   ├── modules/            # Core logic for PDF processing, embeddings, and querying
│   │   ├── main.py         # Main module for processing PDFs and managing embeddings
│   │   ├── utils.py        # Utility functions for loading configuration, embeddings, and similarity calculations
│   │   ├── pdf_processing.py  # Module for extracting text from PDF files and chunking
│   │   └── embedding.py    # Module for generating embeddings using models like GPT or Sentence Transformers
│   ├── config.yaml         # Configuration file for setting model, chunk size, and top-k results
│   ├── main.py             # Entry point for the FastAPI backend app
│   └── requirements.txt    # Python dependencies for backend (FastAPI, Sentence Transformers, etc.)
│
└── frontend/               # Frontend folder (React-based)
    ├── src/                # Source files for the React frontend
    │   ├── components/     # Reusable React components
    │   │   ├── FileUpload.js  # Component for handling file uploads
    │   │   ├── ChatBox.js     # Main component for the chat interface where users can query the document
    │   │   ├── UserImage.js   # Component for displaying the user's avatar in the chat interface
    │   │   ├── LoadingBar.js  # Component for displaying a loading bar during file upload or querying
    │   │   └── Logo.js        # Component for displaying the app's logo
    │   ├── App.js           # Main React component that combines all others and renders the frontend
    │   ├── index.js         # Entry point for React application, rendering the App component
    │   ├── styles/          # CSS and styling files for the UI
    │   │   ├── App.css      # Main CSS file for styling the app
    │   │   ├── normal.css   # CSS reset or normalizing styles for cross-browser consistency
    ├── public/              # Public assets (static files like images)
    │   └── index.html       # HTML template where the React app is injected
    ├── package.json         # npm dependencies and scripts for running the frontend
                 # This README file
```

## Technologies Used

- **FastAPI**: Backend framework for handling API requests.
- **React**: Frontend framework for building the user interface.
- **OpenAI GPT-4**: Used for embeddings and generating answers from document content.
- **Sentence Transformers**: Model for generating embeddings.
- **Axios**: Used in frontend to make API requests.
- **PyTorch**: Backend framework for handling tensor operations and embeddings.

## Contributing

We welcome contributions to improve the project! Here's how you can get involved:

1. Fork the repository.
2. Create a new feature branch: `git checkout -b feature-branch-name`.
3. Commit your changes: `git commit -m 'Add new feature'`.
4. Push the branch: `git push origin feature-branch-name`.
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.


---

### **How to Use This README**:
- Copy and paste this markdown content into a `README.md` file in the root of your project.
- Replace any placeholders such as `yourusername` or the OpenAI model name with the appropriate details specific to your project.
- Add any additional steps or custom configurations if necessary.

Let me know if you need any more details or modifications!