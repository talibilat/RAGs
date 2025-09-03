import os
import dotenv
from openai import OpenAI
from utils.logger import setup_logger

# Set up minimal logger
logger = setup_logger(name="OpenAI_Embeddings", log_to_file=True)

# Load environment variables
dotenv.load_dotenv()

# OpenAI variables
openai_api_key = os.getenv("OPENAI_API_KEY")

def generate_openai_embedding(text):
    """Generate embedding using OpenAI API
    
    Args:
        text (str): Text to generate embedding for
        
    Returns:
        list: Embedding vector
    """
    try:
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        client = OpenAI(api_key=openai_api_key)
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        
        # Extract embedding from response
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        logger.error(f"Error generating OpenAI embedding: {str(e)}")
        raise 