import os
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/rag_ledger")

print("Resetting PostgreSQL 'chunk_embeddings' table...")
engine = create_engine(database_url)
with engine.connect() as conn:
    # Truncate to remove data that conflicts with dimension change
    conn.execute(text("TRUNCATE TABLE chunk_embeddings CASCADE"))
    conn.execute(text("ALTER TABLE chunk_embeddings ALTER COLUMN embedding TYPE vector(1536)"))
    conn.commit()
print("PostgreSQL migration successful.")

print("Deleting Qdrant 'rag_chunks' collection (to reset dimensions)...")
q_client = QdrantClient("localhost", port=6333)
if q_client.collection_exists("rag_chunks"):
    q_client.delete_collection("rag_chunks")
    print("Qdrant collection deleted.")
else:
    print("Qdrant collection does not exist. Skipping.")
