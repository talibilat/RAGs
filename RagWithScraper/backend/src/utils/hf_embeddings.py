import os
import requests
import dotenv
from utils.logger import setup_logger

# Set up minimal logger
logger = setup_logger(name="HuggingFace_Embeddings", log_to_file=True)

# Load environment variables
dotenv.load_dotenv()

# HuggingFace variables
hf_token = os.getenv("HUGGING_FACE_API")
hf_embedding_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

def generate_hf_embedding(text):
    """Generate embedding using Hugging Face API
    
    Args:
        text (str): Text to generate embedding for
        
    Returns:
        list: Embedding vector
    """
    try:
        response = requests.post(
            hf_embedding_url,
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": text}
        )
        
        if response.status_code != 200:
            logger.error(f"Embedding request failed with status code {response.status_code}: {response.text}")
            raise ValueError(f"Request failed with status code {response.status_code}: {response.text}")
            
        return response.json()
    except Exception as e:
        logger.error(f"Error generating HuggingFace embedding: {str(e)}")
        raise 