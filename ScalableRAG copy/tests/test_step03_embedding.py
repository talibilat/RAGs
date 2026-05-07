import pytest
from src.ledger.models import ChunkEmbedding

def test_chunk_embedding_model_has_correct_attributes():
    chunk = ChunkEmbedding(
        chunk_hash="a"*64,
        document_version_id=1,
        text_content="some text",
        structural_path="Report -> Intro",
        embedding=[0.1] * 3072
    )
    
    assert chunk.chunk_hash == "a"*64
    assert chunk.text_content == "some text"
    assert chunk.structural_path == "Report -> Intro"
    assert len(chunk.embedding) == 3072
