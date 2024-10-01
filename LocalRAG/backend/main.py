from fastapi import FastAPI, UploadFile, File, Form, status, HTTPException
import os
import shutil
from modules.utils import load_embeddings, load_config
from modules.main import process_pdf_and_create_embeddings, load_saved_embeddings, query_contract
from fastapi.middleware.cors import CORSMiddleware

# Initialize the FastAPI app
app = FastAPI()

# Enable Cross-Origin Resource Sharing (CORS) to allow requests from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development. Should be restricted in production.
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (including Authorization, Content-Type, etc.)
)

# Directory for uploaded PDF files
UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create directory if it doesn't exist

# Load configuration from a YAML file
config = load_config('config.yaml')

# Endpoint to upload a PDF file
@app.post("/upload/", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF file, save it locally, and process it to generate embeddings.
    """
    # Ensure the uploaded file is a PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")

    # Save the file to the UPLOAD_DIR
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process the PDF to create text chunks and embeddings
    chunks, embeddings = process_pdf_and_create_embeddings(file_path, config)

    # Return a response indicating successful upload and embedding creation
    return {"filename": file.filename, "status": "Embeddings created successfully"}

# Endpoint to handle chatbot queries based on saved embeddings
@app.post("/chatbot/")
async def chatbot(query: str = Form(...)):
    """
    Process a query using pre-saved embeddings from a previously uploaded PDF.
    """
    # Path to the embeddings CSV file
    csv_path = os.path.join(UPLOAD_DIR, "embeddings.csv")

    # Check if embeddings exist; if not, return an error
    if not os.path.exists(csv_path):
        return {"error": "Could not find the file, please upload it again."}

    # Load pre-saved embeddings
    pages_and_chunks, tensor_embeddings = load_saved_embeddings(csv_path)

    # Query the contract using the embeddings
    answer = query_contract(query, tensor_embeddings, pages_and_chunks)

    # Return the query and the generated answer
    return {"query": query, "answer": answer}
