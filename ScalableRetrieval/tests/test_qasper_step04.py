import json
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.datasets.qasper_step04_eval import calculate_metrics, get_sampled_doc_ids, run_step04
from src.ledger.models import Base, ChunkEmbedding, Document, DocumentStatus, DocumentVersion


def test_calculate_metrics():
    # Mock retrieval results (top 10)
    # Legacy qrels may still use chunk IDs as gold evidence.
    results = [{"id": "chunk_1"}, {"id": "chunk_2"}, {"id": "chunk_3"}]
    gold_evidence = ["chunk_2", "chunk_5"]
    
    metrics = calculate_metrics(results, gold_evidence)
    
    # Recall@10: "chunk_2" is in results, "chunk_5" is not. 1/2 = 0.5
    assert metrics["recall@10"] == 0.5
    # chunk_2 is at rank 1 (0-indexed) -> position 2. MRR = 1/2 = 0.5
    assert metrics["mrr@10"] == 0.5


def test_calculate_metrics_matches_pdf_normalized_evidence_text():
    results = [
        {
            "id": "chunk_1",
            "text": "The model evaluates faith-\nfulness with graded criteria in practice.",
        }
    ]
    gold_evidence = ["The model evaluates faithfulness with graded criteria."]

    metrics = calculate_metrics(results, gold_evidence)

    assert metrics["recall@1"] == 1.0
    assert metrics["recall@5"] == 1.0
    assert metrics["recall@10"] == 1.0
    assert metrics["mrr@10"] == 1.0


def test_get_sampled_doc_ids_returns_only_indexed_documents(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ledger.db'}", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)

    with session_factory() as session:
        unindexed_doc = Document(
            filename="doc_unindexed.pdf",
            sha256_hash="a" * 64,
            tenant_id="qasper_eval",
            storage_path="/tmp/doc_unindexed.pdf",
        )
        indexed_doc = Document(
            filename="doc_indexed.pdf",
            sha256_hash="b" * 64,
            tenant_id="qasper_eval",
            storage_path="/tmp/doc_indexed.pdf",
        )
        other_tenant_doc = Document(
            filename="doc_other_tenant.pdf",
            sha256_hash="c" * 64,
            tenant_id="other_tenant",
            storage_path="/tmp/doc_other_tenant.pdf",
        )
        session.add_all([unindexed_doc, indexed_doc, other_tenant_doc])
        session.flush()

        unindexed_version = DocumentVersion(
            document_id=unindexed_doc.id,
            version_hash="d" * 64,
            status=DocumentStatus.PARSED,
        )
        indexed_version = DocumentVersion(
            document_id=indexed_doc.id,
            version_hash="e" * 64,
            status=DocumentStatus.PARSED,
        )
        other_tenant_version = DocumentVersion(
            document_id=other_tenant_doc.id,
            version_hash="f" * 64,
            status=DocumentStatus.PARSED,
        )
        session.add_all([unindexed_version, indexed_version, other_tenant_version])
        session.flush()

        session.add_all(
            [
                ChunkEmbedding(
                    chunk_hash="g" * 64,
                    document_version_id=indexed_version.id,
                    text_content="indexed text",
                    structural_path="body",
                    embedding=[0.0] * 1536,
                ),
                ChunkEmbedding(
                    chunk_hash="h" * 64,
                    document_version_id=other_tenant_version.id,
                    text_content="other tenant text",
                    structural_path="body",
                    embedding=[0.0] * 1536,
                ),
            ]
        )
        session.commit()

    assert get_sampled_doc_ids(session_factory) == {"doc_indexed"}


@patch("src.datasets.qasper_step04_eval.dual_search")
@patch("src.datasets.qasper_step04_eval.rerank_results")
@patch("src.datasets.qasper_step04_eval.AzureEmbeddingClient")
@patch("src.datasets.qasper_step04_eval.build_session_factory_from_url")
def test_run_step04_iterates_questions(
    mock_bf, mock_embed_client_class, mock_rerank, mock_dual_search, tmp_path
):
    # Setup mock gold data
    gold_path = tmp_path / "gold.jsonl"
    gold_data = [
        {
            "query_id": "q1",
            "question": "What is X?",
            "doc_id": "doc1",
            "gold_evidence": ["chunk_1"]
        },
        {
            "query_id": "q2",
            "question": "What is Y?",
            "doc_id": "doc2",
            "gold_evidence": ["chunk_2"]
        }
    ]
    with gold_path.open("w") as f:
        for item in gold_data:
            f.write(json.dumps(item) + "\n")
            
    mock_dual_search.return_value = [{"id": "chunk_1", "text": "text"}]
    mock_rerank.return_value = [{"id": "chunk_1", "text": "text"}]
    
    # Filter for doc1 only
    with patch("src.datasets.qasper_step04_eval.get_sampled_doc_ids") as mock_get_sampled:
        mock_get_sampled.return_value = {"doc1"}
        run_step04(gold_path=gold_path, report_path=tmp_path / "report.json")
    
    assert mock_dual_search.call_count == 1
    assert mock_dual_search.call_args.kwargs["doc_id"] == "doc1"
    assert mock_rerank.call_count == 1


@patch("src.datasets.qasper_step04_eval.dual_search")
@patch("src.datasets.qasper_step04_eval.rerank_results")
@patch("src.datasets.qasper_step04_eval.AzureEmbeddingClient")
@patch("src.datasets.qasper_step04_eval.build_session_factory_from_url")
def test_run_step04_skips_questions_with_empty_gold_evidence(
    mock_bf, mock_embed_client_class, mock_rerank, mock_dual_search, tmp_path
):
    gold_path = tmp_path / "gold.jsonl"
    gold_data = [
        {
            "query_id": "q1",
            "question": "What is X?",
            "doc_id": "doc1",
            "gold_evidence": ["chunk_1"],
        },
        {
            "query_id": "q2",
            "question": "Unsupported?",
            "doc_id": "doc1",
            "gold_evidence": [],
        },
    ]
    with gold_path.open("w") as f:
        for item in gold_data:
            f.write(json.dumps(item) + "\n")

    mock_dual_search.return_value = [{"id": "chunk_1", "text": "text"}]
    mock_rerank.return_value = [{"id": "chunk_1", "text": "text"}]

    with patch("src.datasets.qasper_step04_eval.get_sampled_doc_ids") as mock_get_sampled:
        mock_get_sampled.return_value = {"doc1"}
        run_step04(gold_path=gold_path, report_path=tmp_path / "report.json")

    report = json.loads((tmp_path / "report.json").read_text())
    assert mock_dual_search.call_count == 1
    assert report["evaluated_question_count"] == 1
    assert report["skipped_empty_gold_evidence_count"] == 1


@patch("src.datasets.qasper_step04_eval.dual_search")
@patch("src.datasets.qasper_step04_eval.rerank_results")
@patch("src.datasets.qasper_step04_eval.AzureEmbeddingClient")
@patch("src.datasets.qasper_step04_eval.build_session_factory_from_url")
def test_run_step04_uses_progress_bar_for_evaluation(
    mock_bf, mock_embed_client_class, mock_rerank, mock_dual_search, tmp_path
):
    gold_path = tmp_path / "gold.jsonl"
    gold_path.write_text(
        json.dumps(
            {
                "query_id": "q1",
                "question": "What is X?",
                "doc_id": "doc1",
                "gold_evidence": ["chunk_1"],
            }
        )
        + "\n"
    )
    mock_dual_search.return_value = [{"id": "chunk_1", "text": "text"}]
    mock_rerank.return_value = [{"id": "chunk_1", "text": "text"}]

    with patch("src.datasets.qasper_step04_eval.get_sampled_doc_ids") as mock_get_sampled:
        mock_get_sampled.return_value = {"doc1"}
        with patch("src.datasets.qasper_step04_eval.tqdm", create=True) as mock_tqdm:
            mock_tqdm.side_effect = lambda iterable, **kwargs: iterable
            run_step04(gold_path=gold_path, report_path=tmp_path / "report.json")

    mock_tqdm.assert_called_once()
    assert mock_tqdm.call_args.kwargs["total"] == 1
    assert mock_tqdm.call_args.kwargs["desc"] == "Evaluating questions"
