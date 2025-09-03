"""
Voy Health RAG API Service.

This is the main FastAPI application that serves as the backend for the RAG
(Retrieval-Augmented Generation) system. It provides endpoints for generating
answers to user questions using the RAG pipeline, with comprehensive evaluation
metrics.

The API integrates components from multiple modules:
- retrieval: For fetching relevant documents from vector database
- generation: For generating answers using retrieved context and LLM
- evaluation: For assessing the quality of generated responses

Environment variables:
- OPENAI_API_KEY: API key for OpenAI services
- MONGODB_URI: MongoDB connection string
- API_HOST/API_PORT: Host and port for API server
"""
import os
import sys
import dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict

# Add the src directory to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Import generation function
from generation.generating_output import generate_answer
from utils.logger import setup_logger
from evaluation.evaluator import evaluate_response

# Load environment variables
dotenv.load_dotenv()

# Set up logger
logger = setup_logger(name="RAG API", log_to_file=True)

# Initialize FastAPI app
app = FastAPI(
    title="Voy Health RAG API",
    description="API for generating answers using RAG system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    """
    Request model for question endpoint.
    
    Attributes:
        question (str): The question text from the user
    """
    question: str

class AnswerResponse(BaseModel):
    """
    Response model for answer endpoint.
    
    Attributes:
        answer (str): The generated answer text
        references (List[str]): List of reference URLs for the sources
        success (bool): Whether the generation was successful
        error (Optional[str]): Error message if generation failed
        evaluation (Optional[Dict]): Evaluation metrics for the generated answer
    """
    answer: str
    references: List[str]
    success: bool
    error: Optional[str] = None
    evaluation: Optional[Dict] = None

@app.get("/")
async def root():
    """
    Root endpoint - health check and API information.
    
    Returns:
        Dict: Information about the API service and available endpoints
    """
    return {
        "status": "healthy", 
        "service": "Voy Health RAG API",
        "endpoints": {
            "/": "Health check endpoint",
            "/generate": "Generate answers using RAG system"
        }
    }

@app.post("/generate", response_model=AnswerResponse)
async def generate(request: QuestionRequest):
    """
    Generate an answer for a given question using the RAG system.
    
    This endpoint:
    1. Takes a user question as input
    2. Retrieves relevant documents from the vector database
    3. Generates an answer using the RAG pipeline
    4. Evaluates the quality of the generated answer
    5. Returns the answer, references, and evaluation metrics
    
    Args:
        request (QuestionRequest): The question request object containing the query
        
    Returns:
        AnswerResponse: The generated answer with references, status, and evaluation metrics
        
    Raises:
        HTTPException: If an error occurs during generation
    """
    try:
        logger.info(f"Received question: {request.question}")
        
        # Validate the input question
        if not request.question.strip():
            logger.warning("Received empty question")
            return AnswerResponse(
                answer="Please provide a valid question.",
                references=[],
                success=False,
                error="Question cannot be empty"
            )
        
        # Generate answer using the RAG pipeline
        answer, references = generate_answer(request.question)
        
        # Check if we got a valid answer or an error/fallback response
        if answer.startswith("I apologize"):
            logger.warning("No relevant information found")
            return AnswerResponse(
                answer=answer,
                references=references,
                success=False,
                error="No relevant information found"
            )
        
        # Evaluate the quality of the generated answer
        evaluation = await evaluate_response(
            question=request.question,
            response=answer,
            context=references
        )
        
        logger.info("Successfully generated answer with evaluation metrics")
        return AnswerResponse(
            answer=answer,
            references=references,
            success=True,
            evaluation=evaluation
        )
        
    except Exception as e:
        error_msg = f"Error generating answer: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

if __name__ == "__main__":
    import uvicorn
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True  # Enable auto-reload during development
    )
