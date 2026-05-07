import pytest
import hashlib
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from src.ledger.models import Base, ChunkEmbedding, DocumentVersion, Document, DocumentStatus
from src.ingestion.embedding import ZeroWasteEmbedder

class MockEmbeddingClient:
    def __init__(self):
        self.call_count = 0
        self.texts_embedded = []

    def embed_chunks(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        self.texts_embedded.extend(texts)
        # return dummy 3072-d vectors
        return [[0.1] * 3072 for _ in texts]


@pytest.fixture()
def session_factory():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/rag_ledger", future=True)
    # Ensure pgvector is created
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    yield sessionmaker(bind=engine, future=True)
    
    # Cleanup after test
    Base.metadata.drop_all(engine)

def test_zero_waste_embedder_caches_identical_chunks(session_factory):
    # Setup document version
    with session_factory() as session:
        doc = Document(filename="test.pdf", sha256_hash="abc", tenant_id="tenant-1", storage_path="/tmp")
        session.add(doc)
        session.commit()
        doc_id = doc.id
        version = DocumentVersion(document_id=doc_id, version_hash="abc", status=DocumentStatus.PARSED)
        session.add(version)
        session.commit()
        vid = version.id

    client = MockEmbeddingClient()
    embedder = ZeroWasteEmbedder(client=client, session_factory=session_factory)
    
    chunks = [
        {
            "document_version_id": vid,
            "structural_path": "Root",
            "text_content": "This is a test chunk."
        }
    ]
    
    # First call: Should hit the API
    embedder.embed_and_store(chunks)
    assert client.call_count == 1
    
    # Check DB
    with session_factory() as session:
        db_chunks = session.scalars(select(ChunkEmbedding)).all()
        assert len(db_chunks) == 1
        assert db_chunks[0].text_content == "This is a test chunk."
        expected_hash = hashlib.sha256(b"This is a test chunk.").hexdigest()
        assert db_chunks[0].chunk_hash == expected_hash

    # Second call with the same chunk content: Should NOT hit the API
    embedder.embed_and_store(chunks)
    assert client.call_count == 1 # Still 1!
    
    with session_factory() as session:
        version2 = DocumentVersion(document_id=doc_id, version_hash="def", status=DocumentStatus.PARSED)
        session.add(version2)
        session.commit()
        vid2 = version2.id

    chunks2 = [
        {
            "document_version_id": vid2,
            "structural_path": "Root",
            "text_content": "This is a test chunk."
        }
    ]
    
    embedder.embed_and_store(chunks2)
    assert client.call_count == 1 # Still 1!
    
    # DB should now have 3 chunk_embeddings (1 from first call, 1 from duplicate call, 1 from second doc version)
    with session_factory() as session:
        db_chunks = session.scalars(select(ChunkEmbedding)).all()
        assert len(db_chunks) == 3
