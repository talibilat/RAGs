from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.datasets.qasper_step03_index import build_search_chunk_id, run_step03
from src.ingestion.ingest import ingest_file
from src.ledger.models import Base, ChunkEmbedding, DocumentStatus, DocumentVersion


@patch("src.datasets.qasper_step03_index.sync_to_search_engines")
@patch("src.datasets.qasper_step03_index.ZeroWasteEmbedder")
@patch("src.datasets.qasper_step03_index.AzureEmbeddingClient")
@patch("src.datasets.qasper_step03_index.MarkdownChunker")
@patch("src.datasets.qasper_step03_index.build_session_factory_from_url")
def test_run_step03_chunks_and_indexes(
    mock_bf, mock_chunker_class, mock_embed_client_class, mock_z_embedder_class, mock_sync, tmp_path
):
    # Setup mock parsed files
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    (parsed_dir / "doc1.md").write_text("# Title\nContent")
    
    mock_chunker = MagicMock()
    mock_chunker_class.return_value = mock_chunker
    mock_chunker.chunk_document.return_value = [{"text_content": "chunk", "document_version_id": 1, "structural_path": "root"}]
    
    # Mock the ZeroWasteEmbedder to return something or just succeed
    mock_z_embedder = MagicMock()
    mock_z_embedder_class.return_value = mock_z_embedder
    
    # We need to mock the DB query that gets the document_version_id from the doc_id (filename)
    with patch("src.datasets.qasper_step03_index.get_version_id_by_doc_id") as mock_get_vid:
        mock_get_vid.return_value = 42
        with patch("src.datasets.qasper_step03_index.document_version_has_chunks") as mock_has_chunks:
            mock_has_chunks.return_value = False
            with patch("src.datasets.qasper_step03_index.get_source_doc_id_by_version_id") as mock_doc_id:
                mock_doc_id.return_value = "doc1"
                with patch("src.datasets.qasper_step03_index.get_chunks_for_version") as mock_chunks:
                    mock_chunks.return_value = [
                        SimpleNamespace(
                            document_version_id=42,
                            chunk_hash="a" * 64,
                            text_content="chunk",
                            embedding=[0.0] * 1536,
                            structural_path="root",
                        )
                    ]
                    run_step03(parsed_dir=parsed_dir, database_url="sqlite:///:memory:")
    
    assert mock_chunker.chunk_document.call_count == 1
    assert mock_sync.call_count == 1
    sync_payload = mock_sync.call_args.args[1]
    assert sync_payload[0]["chunk_id"] == build_search_chunk_id(42, sync_payload[0]["chunk_hash"])
    assert sync_payload[0]["doc_id"] == "doc1"
    assert sync_payload[0]["document_version_id"] == 42


@patch("src.datasets.qasper_step03_index.sync_to_search_engines")
@patch("src.datasets.qasper_step03_index.ZeroWasteEmbedder")
@patch("src.datasets.qasper_step03_index.AzureEmbeddingClient")
@patch("src.datasets.qasper_step03_index.MarkdownChunker")
@patch("src.datasets.qasper_step03_index.build_session_factory_from_url")
def test_run_step03_uses_progress_bar_for_markdown_files(
    mock_bf, mock_chunker_class, mock_embed_client_class, mock_z_embedder_class, mock_sync, tmp_path
):
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    (parsed_dir / "doc1.md").write_text("# Title\nContent")

    mock_chunker = MagicMock()
    mock_chunker_class.return_value = mock_chunker
    mock_chunker.chunk_document.return_value = [{"text_content": "chunk"}]
    mock_z_embedder_class.return_value = MagicMock()

    with patch("src.datasets.qasper_step03_index.get_version_id_by_doc_id") as mock_get_vid:
        mock_get_vid.return_value = 42
        with patch("src.datasets.qasper_step03_index.document_version_has_chunks") as mock_has_chunks:
            mock_has_chunks.return_value = False
            with patch("src.datasets.qasper_step03_index.get_source_doc_id_by_version_id") as mock_doc_id:
                mock_doc_id.return_value = "doc1"
                with patch("src.datasets.qasper_step03_index.get_chunks_for_version") as mock_chunks:
                    mock_chunks.return_value = []
                    with patch("src.datasets.qasper_step03_index.tqdm", create=True) as mock_tqdm:
                        mock_tqdm.side_effect = lambda iterable, **kwargs: iterable
                        run_step03(parsed_dir=parsed_dir, database_url="sqlite:///:memory:")

    mock_tqdm.assert_called_once()
    assert mock_tqdm.call_args.kwargs["total"] == 1
    assert mock_tqdm.call_args.kwargs["desc"] == "Indexing markdown"


@patch("src.datasets.qasper_step03_index.sync_to_search_engines")
@patch("src.datasets.qasper_step03_index.ZeroWasteEmbedder")
@patch("src.datasets.qasper_step03_index.AzureEmbeddingClient")
@patch("src.datasets.qasper_step03_index.MarkdownChunker")
def test_run_step03_skips_document_versions_that_already_have_chunks(
    mock_chunker_class, mock_embed_client_class, mock_z_embedder_class, mock_sync, tmp_path
):
    parsed_dir = tmp_path / "parsed"
    parsed_dir.mkdir()
    source_pdf = tmp_path / "incoming" / "doc1.pdf"
    source_pdf.parent.mkdir()
    source_pdf.write_bytes(b"%PDF-1.7\nsource")

    engine = create_engine(f"sqlite:///{tmp_path / 'ledger.db'}", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    ingest_result = ingest_file(source_pdf, tmp_path / "raw", "qasper_eval", session_factory)
    with session_factory() as session:
        version = session.scalars(
            select(DocumentVersion).where(DocumentVersion.document_id == ingest_result.document_id)
        ).one()
        version.status = DocumentStatus.PARSED
        session.add(
            ChunkEmbedding(
                chunk_hash="a" * 64,
                document_version_id=version.id,
                text_content="already indexed",
                structural_path="body",
                embedding=[0.0] * 1536,
            )
        )
        session.commit()

    (parsed_dir / f"{ingest_result.document_id}.md").write_text("# Title\nContent")

    run_step03(
        parsed_dir=parsed_dir,
        database_url=f"sqlite:///{tmp_path / 'ledger.db'}",
    )

    mock_chunker_class.return_value.chunk_document.assert_not_called()
    mock_z_embedder_class.return_value.embed_and_store.assert_not_called()
    mock_sync.assert_called_once()
