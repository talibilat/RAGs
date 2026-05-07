import json
from pathlib import Path

from src.datasets.qasper_step00 import (
    Step00Paths,
    build_manifest_entry,
    content_hash_for_document,
    generate_fallback_pdf,
    normalize_document,
    validate_outputs,
)


def _sample_paper() -> dict:
    return {
        "id": "paper-1",
        "title": "A Retrieval Paper",
        "abstract": "This paper studies retrieval.",
        "full_text": [
            {
                "section_name": "Introduction",
                "paragraphs": [
                    "Retrieval systems find evidence.",
                    "Evidence supports answers.",
                ],
            }
        ],
        "figures_and_tables": [{"caption": "An example table.", "file": "table1.png"}],
        "qas": [
            {
                "question": "What do retrieval systems find?",
                "question_id": "q1",
                "answers": [
                    {
                        "annotation_id": "a1",
                        "worker_id": "w1",
                        "answer": {
                            "unanswerable": False,
                            "extractive_spans": ["evidence"],
                            "yes_no": None,
                            "free_form_answer": "",
                            "evidence": ["Retrieval systems find evidence."],
                            "highlighted_evidence": ["find evidence"],
                        },
                    },
                    {
                        "annotation_id": "a2",
                        "worker_id": "w2",
                        "answer": {
                            "unanswerable": False,
                            "extractive_spans": [],
                            "yes_no": None,
                            "free_form_answer": "They find supporting evidence.",
                            "evidence": ["Evidence supports answers."],
                            "highlighted_evidence": [],
                        },
                    },
                ],
            },
            {
                "question": "Is the result unavailable?",
                "question_id": "q2",
                "answers": [
                    {
                        "annotation_id": "a3",
                        "worker_id": "w3",
                        "answer": {
                            "unanswerable": True,
                            "extractive_spans": [],
                            "yes_no": None,
                            "free_form_answer": "",
                            "evidence": [],
                            "highlighted_evidence": [],
                        },
                    }
                ],
            },
        ],
    }


def test_normalize_document_preserves_qasper_schema_and_all_answer_annotations():
    document, qa_rows = normalize_document(_sample_paper(), split="train")

    assert document["doc_id"] == "paper-1"
    assert document["split"] == "train"
    assert document["sections"] == [
        {
            "section_name": "Introduction",
            "paragraphs": [
                "Retrieval systems find evidence.",
                "Evidence supports answers.",
            ],
        }
    ]
    assert document["figures_and_tables"][0]["caption"] == "An example table."
    assert len(qa_rows) == 2
    assert qa_rows[0]["query_id"] == "paper-1::q1"
    assert qa_rows[0]["gold_answers"] == ["evidence", "They find supporting evidence."]
    assert qa_rows[0]["gold_evidence"] == [
        "Retrieval systems find evidence.",
        "Evidence supports answers.",
    ]
    assert qa_rows[0]["answer_type"] == "extractive"
    assert qa_rows[1]["answer_type"] == "unanswerable"
    assert qa_rows[1]["is_unanswerable"] is True


def test_normalize_document_accepts_huggingface_column_oriented_sequences():
    raw = _sample_paper()
    raw["full_text"] = {
        "section_name": ["Introduction"],
        "paragraphs": [["Retrieval systems find evidence."]],
    }
    raw["qas"] = {
        "question": ["What is found?"],
        "question_id": ["q1"],
        "answers": [
            {
                "answer": [
                    {
                        "unanswerable": False,
                        "extractive_spans": ["evidence"],
                        "yes_no": None,
                        "free_form_answer": "",
                        "evidence": ["Retrieval systems find evidence."],
                        "highlighted_evidence": ["find evidence"],
                    }
                ],
                "annotation_id": ["a1"],
                "worker_id": ["w1"],
            }
        ],
    }
    raw["figures_and_tables"] = {"caption": ["Figure caption."], "file": ["fig1.png"]}

    document, qa_rows = normalize_document(raw, split="validation")

    assert document["sections"] == [
        {"section_name": "Introduction", "paragraphs": ["Retrieval systems find evidence."]}
    ]
    assert document["figures_and_tables"] == [{"caption": "Figure caption.", "file": "fig1.png"}]
    assert qa_rows[0]["gold_answers"] == ["evidence"]
    assert qa_rows[0]["gold_evidence"] == ["Retrieval systems find evidence."]


def test_generate_fallback_pdf_writes_pdf_with_provenance(tmp_path):
    document, _ = normalize_document(_sample_paper(), split="train")
    output_path = tmp_path / "paper-1.pdf"

    generate_fallback_pdf(document, output_path)

    payload = output_path.read_bytes()
    assert payload.startswith(b"%PDF-1.4")
    assert b"Generated from QASPER structured full text" in payload
    assert b"paper-1" in payload


def test_build_manifest_entry_records_pdf_provenance_and_counts(tmp_path):
    document, qa_rows = normalize_document(_sample_paper(), split="train")
    pdf_path = tmp_path / "paper-1.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nsample\n%%EOF\n")

    entry = build_manifest_entry(
        document=document,
        qa_rows=qa_rows,
        pdf_path=pdf_path,
        pdf_type="generated",
        pdf_source_url=None,
        qasper_source="https://huggingface.co/datasets/allenai/qasper",
        licence="cc-by-4.0",
        download_status="generated",
        notes="Generated from structured full text.",
    )

    assert entry["doc_id"] == "paper-1"
    assert entry["pdf_type"] == "generated"
    assert entry["sha256"]
    assert entry["content_hash"] == content_hash_for_document(document)
    assert entry["has_questions"] is True
    assert entry["num_questions"] == 2
    assert entry["num_answers"] == 3
    assert entry["num_gold_evidence_items"] == 2


def test_validate_outputs_rejects_missing_pdf_and_accepts_ready_dataset(tmp_path):
    paths = Step00Paths(root=tmp_path)
    paths.ensure()
    document, qa_rows = normalize_document(_sample_paper(), split="train")
    pdf_path = paths.generated_pdf_dir / "paper-1.pdf"
    generate_fallback_pdf(document, pdf_path)

    manifest = [
        build_manifest_entry(
            document=document,
            qa_rows=qa_rows,
            pdf_path=pdf_path,
            pdf_type="generated",
            pdf_source_url=None,
            qasper_source="https://huggingface.co/datasets/allenai/qasper",
            licence="cc-by-4.0",
            download_status="generated",
            notes="Generated from structured full text.",
        )
    ]
    paths.manifest_path.write_text(json.dumps({"documents": manifest}), encoding="utf-8")
    paths.eval_qa_path.write_text(
        "\n".join(json.dumps(row) for row in qa_rows) + "\n",
        encoding="utf-8",
    )

    summary = validate_outputs(paths, min_usable_pdfs=1)

    assert summary["total_qasper_documents"] == 1
    assert summary["total_usable_pdfs"] == 1
    assert summary["fallback_pdfs_generated"] == 1
    assert summary["validation_errors"] == []

    pdf_path.unlink()
    broken = validate_outputs(paths, min_usable_pdfs=1)
    assert any("PDF path does not exist" in error for error in broken["validation_errors"])
