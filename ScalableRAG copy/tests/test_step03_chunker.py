import pytest
from src.ingestion.chunker import MarkdownChunker

def test_markdown_chunker_splits_headers_and_preserves_metadata():
    markdown_text = """# Header 1
This is the first paragraph.

## Header 2
This is the second paragraph.
"""
    
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document(
        text=markdown_text,
        document_version_id=42
    )
    
    assert len(chunks) == 2
    assert chunks[0]["document_version_id"] == 42
    assert chunks[0]["structural_path"] == "Header 1"
    assert chunks[0]["text_content"].strip() == "This is the first paragraph."
    
    assert chunks[1]["document_version_id"] == 42
    assert chunks[1]["structural_path"] == "Header 1 -> Header 2"
    assert chunks[1]["text_content"].strip() == "This is the second paragraph."


def test_markdown_chunker_preserves_tenant_metadata():
    chunker = MarkdownChunker()

    chunks = chunker.chunk_document(
        text="# Root\nTenant scoped content.",
        document_version_id=7,
        tenant_id="tenant-a",
    )

    assert chunks == [
        {
            "document_version_id": 7,
            "tenant_id": "tenant-a",
            "structural_path": "Root",
            "text_content": "Tenant scoped content.",
        }
    ]


def test_section_aware_chunker_splits_oversized_sections_for_embedding_limit():
    chunker = MarkdownChunker(strategy="section_aware")
    text = "# Long Section\n" + ("token " * 9000)

    chunks = chunker.chunk_document(text, 1)

    assert len(chunks) > 1
    assert all(len(chunk["text_content"]) <= 6000 for chunk in chunks)
    assert {chunk["structural_path"] for chunk in chunks} == {"Long Section"}


def test_markdown_chunker_fixed_size_300():
    chunker = MarkdownChunker(strategy="fixed_300_overlap_50")
    text = "Word " * 600 # Roughly 3000 characters
    chunks = chunker.chunk_document(text, 1)
    # Check that it produces multiple chunks
    assert len(chunks) > 1
    # Check that chunks are roughly the requested size
    assert len(chunks[0]["text_content"].split()) <= 400 # Allow some margin


def test_markdown_chunker_fixed_size_600():
    chunker = MarkdownChunker(strategy="fixed_600_overlap_100")
    text = "Word " * 1200 # Roughly 6000 characters
    chunks = chunker.chunk_document(text, 1)
    assert len(chunks) > 1
    assert len(chunks[0]["text_content"].split()) <= 800
