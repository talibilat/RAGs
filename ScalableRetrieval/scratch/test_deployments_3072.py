from openai import AzureOpenAI
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_KEY")

parsed = urlparse(endpoint)
base_endpoint = f"{parsed.scheme}://{parsed.netloc}/"

client = AzureOpenAI(
    api_key=key,
    api_version="2023-05-15",
    azure_endpoint=base_endpoint
)

# Common names for 3072-dim models
deployments = ["text-embedding-3-large", "embedding-large", "large-embedding", "text-embedding-v3-large"]

for dep in deployments:
    try:
        print(f"Testing deployment: {dep}...")
        client.embeddings.create(input=["test"], model=dep)
        print(f"SUCCESS: {dep} works!")
        break
    except Exception as e:
        print(f"FAILED: {dep}")
else:
    print("No 3072-dim deployment found with common names.")
