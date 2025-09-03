import os
import sys

# Add the src directory to the Python path to enable imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, src_dir)

# Import utilities
from utils.logger import setup_logger
from utils.mongo_client import get_collection
from utils.retriever_client import retrieve_similar_documents

# Set up logger
logger = setup_logger(name="FAQ Retrieval", log_to_file=True)

# Get MongoDB collection
faqs_collection = get_collection("manual", "faqs_regex")
logger.info(f"Connected to MongoDB collection: faqs_regex")



# Example query
query = "Where is my order?"
logger.info(f"Searching for: '{query}'")

# Retrieve similar documents using HuggingFace embeddings
results = retrieve_similar_documents(query, "openai", 4)

print(f"\nResults for query: '{query}' using HuggingFace embeddings:\n")
for i, document in enumerate(results):
    print(f"Result {i+1}:")
    print(f"Question: {document['question']}")
    print(f"Answer: {document['answer']}")
    print(f"Link: {document['page_url']}")
    print(f"Title: {document['page_title']}")
    print("")

