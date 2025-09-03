import os
import sys

# Add the src directory to the Python path to enable imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, src_dir)

# Import utilities
from utils.logger import setup_logger
from utils.mongo_client import get_collection
from utils.hf_embeddings import generate_hf_embedding 
from utils.openai_embeddings import generate_openai_embedding

# Set up logger
logger = setup_logger(name="FAQ Embedding Generation", log_to_file=True)

# Get MongoDB collection
faqs_collection = get_collection("manual", "faqs_regex")
logger.info(f"Connected to MongoDB collection: faqs_regex")

def generate_embedding(text, embedding_type):
    """Generate embedding based on the specified type
    
    Args:
        text (str): Text to generate embedding for
        embedding_type (str): Type of embedding to generate ("hf" or "openai")
        
    Returns:
        list: Embedding vector
    """
    if embedding_type == "hf":
        return generate_hf_embedding(text)
    elif embedding_type == "openai":
        return generate_openai_embedding(text)
    else:
        raise ValueError(f"Unknown embedding type: {embedding_type}")


# Find documents that need embeddings
logger.info("Starting embedding generation process for documents...")
docs_count = faqs_collection.count_documents({'content':{"$exists": True}})
logger.info(f"Found {docs_count} documents with 'content' field")

    
# Process each document
processed_count = 0
error_count = 0

for doc in faqs_collection.find({'content':{"$exists": True}}):
    try:
        doc_id = str(doc['_id'])
        logger.info(f"Processing document {processed_count+1}/{docs_count}, ID: {doc_id}")
        
        # Generate embedding
        embedding_type = "openai"  # You can change this to "openai" if needed
        embedding_field = f"content_embedding_{embedding_type}"
        
        doc[embedding_field] = generate_embedding(doc['content'], embedding_type)
        
        # Update document in database
        result = faqs_collection.replace_one({'_id': doc['_id']}, doc)
        
        if result.modified_count == 1:
            logger.info(f"Successfully updated document with {embedding_type} embedding, ID: {doc_id}")
        else:
            logger.warning(f"Document was not modified, ID: {doc_id}")
        
        processed_count += 1
    except Exception as e:
        error_count += 1
        logger.error(f"Error processing document {str(doc['_id'])}: {str(e)}")

logger.info(f"Embedding generation complete. Processed {processed_count} documents successfully, {error_count} errors.")
