"""
This script demonstrates how to create a proper RAG chain without using the temperature parameter,
which is causing the BadRequestError for certain models.
"""

import os
import dotenv
from typing import List

from langchain.chains import RetrievalQA
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pymongo import MongoClient
import certifi

# Load environment variables
dotenv.load_dotenv()

def get_mongodb_client():
    """Get a properly configured MongoDB client."""
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is not set")
    
    try:
        # Use certifi's SSL certificate bundle
        client = MongoClient(
            mongodb_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            appname="talib.rag"
        )
        
        # Verify the connection by issuing a ping
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas")
        return client
    except Exception as e:
        print(f"Connection to MongoDB failed: {e}")
        
        # Fallback to allowing invalid certificates if needed
        print("Trying fallback connection with tlsAllowInvalidCertificates=True")
        try:
            client = MongoClient(
                mongodb_uri,
                tls=True,
                tlsAllowInvalidCertificates=True,
                appname="talib.rag"
            )
            client.admin.command('ping')
            print("Successfully connected to MongoDB Atlas with invalid certificates allowed")
            return client
        except Exception as e2:
            print(f"Fallback connection also failed: {e2}")
            raise

def get_retriever(model: str, k: int) -> VectorStoreRetriever:
    """
    Given an embedding model and top k, get a vector store retriever object

    Args:
        model (str): Embedding model to use
        k (int): Number of results to retrieve

    Returns:
        VectorStoreRetriever: A vector store retriever object
    """
    DB_NAME = "talib"
    client = get_mongodb_client()
    
    embeddings = OpenAIEmbeddings(model=model)

    vector_store = MongoDBAtlasVectorSearch(
        collection=client[DB_NAME][model],
        embedding=embeddings,
        index_name="default",  # Use your actual index name
        text_key="text",
        embedding_key="embedding"
    )

    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": k}
    )
    return retriever

def get_rag_chain(retriever: VectorStoreRetriever, model_name: str = "gpt-4o"):
    """
    Create a RAG chain without using the temperature parameter which
    may cause errors with certain models.
    
    Args:
        retriever: The document retriever
        model_name: OpenAI model to use
        
    Returns:
        A RetrievalQA chain
    """
    # Initialize the ChatOpenAI model WITHOUT temperature parameter
    # This fixes the "Unsupported parameter: 'temperature' is not supported with this model" error
    llm = ChatOpenAI(model=model_name)
    
    # Create the RAG chain
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        verbose=True
    )
    
    return rag_chain

# Example usage
if __name__ == "__main__":
    # Get retriever
    retriever = get_retriever("text-embedding-3-small", 5)
    
    # Create RAG chain without temperature parameter
    rag_chain = get_rag_chain(retriever)
    
    # Test the chain
    query = "What is Wegovy?"
    result = rag_chain.invoke(query)
    
    print(f"\nQuery: {query}")
    print(f"Answer: {result['result']}")
    print("\nSource Documents:")
    for i, doc in enumerate(result["source_documents"]):
        print(f"{i+1}. {doc.page_content[:100]}...") 