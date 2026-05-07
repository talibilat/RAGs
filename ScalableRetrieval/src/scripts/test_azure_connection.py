import os
import sys
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    # Strip everything after .com if present
    if ".com" in endpoint:
        endpoint = endpoint.split(".com")[0] + ".com"
    
    key = os.getenv("AZURE_OPENAI_KEY")
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    
    print(f"Testing Azure OpenAI Connection...")
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    
    try:
        client = AzureOpenAI(
            api_key=key,
            api_version="2023-05-15",
            azure_endpoint=endpoint
        )
        
        response = client.embeddings.create(
            input=["Hello world"],
            model=deployment
        )
        
        embedding = response.data[0].embedding
        print(f"✅ Success! Embedding dimension: {len(embedding)}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_connection()
