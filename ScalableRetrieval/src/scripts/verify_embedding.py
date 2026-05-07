import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.ledger.models import Base, Document, DocumentVersion, DocumentStatus
from src.config.settings import settings
from src.ingestion.chunker import MarkdownChunker
from src.ingestion.embedding import ZeroWasteEmbedder

class TracingEmbeddingClient:
    def __init__(self):
        self.call_count = 0

    def embed_chunks(self, texts: list[str]) -> list[list[float]]:
        print(f"[API Trace] Calling Azure OpenAI API for {len(texts)} chunks...")
        self.call_count += len(texts)
        # return dummy 3072-d vectors
        return [[0.1] * 3072 for _ in texts]

def run_verification():
    print("=== Step 03: Verification Log ===")
    
    # 1. Setup DB
    engine = create_engine(settings.postgres_dsn)
    
    # Run migrations manually for this test
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)
    
    session_factory = sessionmaker(bind=engine)
    
    # Cleanup any previous runs
    with session_factory() as session:
        session.execute(text("TRUNCATE chunk_embeddings, document_versions, documents CASCADE"))
        session.commit()
    
    # 2. Setup Services
    chunker = MarkdownChunker()
    client = TracingEmbeddingClient()
    embedder = ZeroWasteEmbedder(client, session_factory)
    
    markdown_doc = """# Introduction
This is the first paragraph of the report. It contains some boilerplate text.

## Financials
Q3 Revenue was up by 15%.
"""
    
    # --- RUN 1 ---
    print("\n[Run 1] Initial Ingestion")
    with session_factory() as session:
        doc1 = Document(filename="report1.md", sha256_hash="hash1", tenant_id="t1", storage_path="/path1")
        session.add(doc1)
        session.commit()
        ver1 = DocumentVersion(document_id=doc1.id, version_hash="hash1", status=DocumentStatus.PARSED)
        session.add(ver1)
        session.commit()
        vid1 = ver1.id

    chunks1 = chunker.chunk_document(markdown_doc, vid1)
    print(f"Generated {len(chunks1)} chunks.")
    embedder.embed_and_store(chunks1)
    print(f"Total API chunks embedded so far: {client.call_count}")
    
    # --- RUN 2 ---
    print("\n[Run 2] Re-ingestion of the exact same document")
    with session_factory() as session:
        doc2 = Document(filename="report2.md", sha256_hash="hash2", tenant_id="t1", storage_path="/path2")
        session.add(doc2)
        session.commit()
        ver2 = DocumentVersion(document_id=doc2.id, version_hash="hash2", status=DocumentStatus.PARSED)
        session.add(ver2)
        session.commit()
        vid2 = ver2.id
        
    chunks2 = chunker.chunk_document(markdown_doc, vid2)
    print(f"Generated {len(chunks2)} chunks.")
    
    start_calls = client.call_count
    embedder.embed_and_store(chunks2)
    calls_this_run = client.call_count - start_calls
    
    print(f"Calls to Azure OpenAI API during Run 2: {calls_this_run} ( explicitly citing cache hits )")
    print(f"Total API chunks embedded so far: {client.call_count}")

if __name__ == "__main__":
    run_verification()
