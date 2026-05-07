import os
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/rag_ledger")

print("Migrating PostgreSQL 'chunk_embeddings' column to 1536 dimensions...")
engine = create_engine(database_url)
with engine.connect() as conn:
    # Disable autocommit to handle DDL
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
