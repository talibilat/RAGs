"""
Vector Retrieval Client for RAG System.

This module provides functionality for retrieving relevant documents from a MongoDB
vector database using semantic search. It supports multiple embedding models:

1. OpenAI embeddings (text-embedding-ada-002)
2. HuggingFace embeddings (sentence-transformers)

The module connects to a MongoDB collection containing pre-embedded documents and
performs vector similarity search to find the most semantically relevant documents
for a given query.
"""
import os
import dotenv
from utils.logger import setup_logger
from utils.mongo_client import get_collection
from utils.hf_embeddings import generate_hf_embedding 
from utils.openai_embeddings import generate_openai_embedding 

# Load environment variables
dotenv.load_dotenv()

# Set up logger
logger = setup_logger(name="FAQ Retriever", log_to_file=True)

# Get MongoDB collection with pre-embedded documents
faqs_collection = get_collection(
    os.getenv('MONGODB_DATABASE', 'manual'),
    os.getenv('MONGODB_COLLECTION_FAQS', 'faqs_regex')
)
logger.info(f"Connected to MongoDB collection: {os.getenv('MONGODB_COLLECTION_FAQS', 'faqs_regex')}")

def retrieve_similar_documents(query: str, embedding_type: str, limit: int) -> list:
    """
    Retrieve semantically similar documents using vector search.
    
    This function performs the following steps:
    1. Generates an embedding for the input query using the specified embedding model
    2. Performs vector similarity search against the MongoDB collection
    3. Returns the most relevant documents based on semantic similarity
    
    The function supports two embedding types:
    - "hf": HuggingFace sentence-transformers embeddings
    - "openai": OpenAI text-embedding-ada-002 embeddings
    
    Args:
        query (str): The user's question or search query
        embedding_type (str): Type of embedding to use ("hf" or "openai")
        limit (int): Maximum number of documents to return
        
    Returns:
        list: List of document dictionaries containing:
            - question: The question in the document
            - answer: The answer/content
            - page_url: URL of the source page
            - page_title: Title of the source page
            - content: The full document content
            - content_embedding_*: The vector embedding (type depends on embedding_type)
            
    Raises:
        ValueError: If an unsupported embedding type is specified
        Exception: For any errors during the retrieval process
    """
    try:
        logger.info(f"Retrieving documents for query: '{query}' using {embedding_type} embeddings")
        
        # Generate embedding for query using the specified model
        if embedding_type == "hf":
            query_embedding = generate_hf_embedding(query)
            embedding_field = "content_embedding_hf"
            index_name = os.getenv('MONGODB_VECTOR_INDEX_HF', 'faqSemanticSearch')
        elif embedding_type == "openai":
            query_embedding = generate_openai_embedding(query)
            embedding_field = "content_embedding_openai"
            index_name = os.getenv('MONGODB_VECTOR_INDEX_OPENAI', 'faqOpenAISemanticSeachRegex')
        else:
            logger.error(f"Unsupported embedding type: {embedding_type}")
            raise ValueError(f"Unsupported embedding type: {embedding_type}")
        
        logger.debug(f"Generated {embedding_type} embedding for query")
        
        # Verify that documents with the correct embedding field exist
        sample_doc = faqs_collection.find_one({embedding_field: {"$exists": True}})
        if not sample_doc:
            logger.error(f"No documents found with {embedding_field} embeddings")
            return []
            
        # Construct MongoDB vector search aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": query_embedding,
                    "path": embedding_field,
                    "numCandidates": int(os.getenv('MONGODB_VECTOR_NUM_CANDIDATES', 100)),
                    "limit": limit,
                    "index": index_name,
                }
            }
        ]
        
        logger.debug(f"Executing vector search with pipeline: {pipeline}")
        
        # Execute the search and collect results
        results = list(faqs_collection.aggregate(pipeline))
        
        if not results:
            logger.warning(f"No results found for query: '{query}'")
        else:
            logger.info(f"Found {len(results)} results for query: '{query}'")
            
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving similar documents: {str(e)}")
        raise 