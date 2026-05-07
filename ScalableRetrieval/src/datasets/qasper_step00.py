from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal


QASPER_HF_URL = "https://huggingface.co/datasets/allenai/qasper"
QASPER_DATASET_NAME = "allenai/qasper"
QASPER_LICENSE = "cc-by-4.0"
PDF_PROVENANCE_TEXT = "Generated from QASPER structured full text for evaluation ingestion."


PdfType = Literal["original", "generated"]


@dataclass(frozen=True)
class Step00Paths:
    root: Path = Path(".")

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def raw_qasper_dir(self) -> Path:
        return self.data_dir / "raw" / "qasper"

    @property
    def original_pdf_dir(self) -> Path:
        return self.data_dir / "raw" / "pdfs" / "original"

    @property
    def generated_pdf_dir(self) -> Path:
        return self.data_dir / "raw" / "pdfs" / "generated"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def eval_dir(self) -> Path:
        return self.data_dir / "eval"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def processed_documents_path(self) -> Path:
        return self.processed_dir / "qasper_documents.jsonl"

    @property
    def processed_qa_path(self) -> Path:
        return self.processed_dir / "qasper_qa_gold.jsonl"

    @property
    def eval_qa_path(self) -> Path:
        return self.eval_dir / "qasper_qa_gold.jsonl"

    @property
    def manifest_path(self) -> Path:
        return self.data_dir / "manifest.json"

    @property
    def failures_path(self) -> Path:
        return self.reports_dir / "pdf_resolution_failures.jsonl"

    @property
    def summary_json_path(self) -> Path:
        return self.reports_dir / "step00_dataset_summary.json"

    @property
    def summary_md_path(self) -> Path:
        return self.reports_dir / "step00_dataset_summary.md"

    def ensure(self) -> None:
        for path in (
            self.raw_qasper_dir,
            self.original_pdf_dir,
            self.generated_pdf_dir,
            self.processed_dir,
            self.eval_dir,
            self.reports_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_hash_for_document(document: dict[str, Any]) -> str:
    payload = {
        "doc_id": document["doc_id"],
        "title": document.get("title", ""),
        "abstract": document.get("abstract", ""),
        "sections": document.get("sections", []),
        "figures_and_tables": document.get("figures_and_tables", []),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_document(raw_paper: dict[str, Any], split: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    doc_id = str(raw_paper.get("id") or raw_paper.get("doc_id") or raw_paper.get("paper_id"))
    raw_sections = _sequence_records(raw_paper.get("full_text") or [])
    sections = [
        {
            "section_name": str(section.get("section_name") or ""),
            "paragraphs": [str(paragraph) for paragraph in section.get("paragraphs") or []],
        }
        for section in raw_sections
    ]
    qas = _sequence_records(raw_paper.get("qas") or [])
    figures_and_tables = _sequence_records(raw_paper.get("figures_and_tables") or [])
    document = {
        "doc_id": doc_id,
        "paper_id": doc_id,
        "split": split,
        "title": str(raw_paper.get("title") or ""),
        "abstract": str(raw_paper.get("abstract") or ""),
        "full_text": raw_sections,
        "sections": sections,
        "section_names": [section["section_name"] for section in sections],
        "figures_and_tables": figures_and_tables,
        "questions": qas,
        "metadata": _extract_metadata(raw_paper),
        "source": "qasper",
    }
    return document, [_normalize_qa_row(doc_id, split, qa) for qa in qas]


def _sequence_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []
    lengths = [len(item) for item in value.values() if isinstance(item, list)]
    if not lengths:
        return [value]
    row_count = min(lengths)
    records: list[dict[str, Any]] = []
    for index in range(row_count):
        record: dict[str, Any] = {}
        for key, column in value.items():
            record[key] = column[index] if isinstance(column, list) else column
        records.append(record)
    return records


def _normalize_qa_row(doc_id: str, split: str, qa: dict[str, Any]) -> dict[str, Any]:
    question_id = str(qa.get("question_id") or qa.get("id") or qa.get("question") or "")
    answer_items = _answer_annotation_records(qa.get("answers") or [])
    annotations = [_answer_payload(item) for item in answer_items]
    gold_answers: list[str] = []
    gold_evidence: list[str] = []
    highlighted_evidence: list[str] = []
    answer_types: list[str] = []
    is_unanswerable = False

    for annotation in annotations:
        if annotation.get("unanswerable"):
            is_unanswerable = True
            answer_types.append("unanswerable")
        else:
            answer_types.append(_answer_type(annotation))
        gold_answers.extend(_gold_answers(annotation))
        gold_evidence.extend(str(item) for item in annotation.get("evidence") or [])
        highlighted_evidence.extend(str(item) for item in annotation.get("highlighted_evidence") or [])

    return {
        "query_id": f"{doc_id}::{question_id}",
        "doc_id": doc_id,
        "split": split,
        "question": str(qa.get("question") or ""),
        "gold_answers": _dedupe_preserving_order(gold_answers),
        "gold_evidence": _dedupe_preserving_order(gold_evidence),
        "highlighted_evidence": _dedupe_preserving_order(highlighted_evidence),
        "answer_type": _dominant_answer_type(answer_types),
        "is_unanswerable": is_unanswerable and not gold_answers,
        "annotations": answer_items,
        "source": "qasper",
    }


def _answer_annotation_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return _sequence_records(value)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _answer_payload(item: dict[str, Any]) -> dict[str, Any]:
    answer = item.get("answer")
    return answer if isinstance(answer, dict) else item


def _answer_type(answer: dict[str, Any]) -> str:
    if answer.get("unanswerable"):
        return "unanswerable"
    if answer.get("yes_no") is not None:
        return "yes_no"
    if answer.get("extractive_spans"):
        return "extractive"
    if str(answer.get("free_form_answer") or "").strip():
        return "abstractive"
    return "abstractive"


def _dominant_answer_type(answer_types: list[str]) -> str:
    for answer_type in ("extractive", "abstractive", "yes_no", "unanswerable"):
        if answer_type in answer_types:
            return answer_type
    return "abstractive"


def _gold_answers(answer: dict[str, Any]) -> list[str]:
    if answer.get("unanswerable"):
        return []
    if answer.get("extractive_spans"):
        return [str(item) for item in answer["extractive_spans"]]
    if answer.get("yes_no") is not None:
        return ["yes" if answer.get("yes_no") else "no"]
    free_form = str(answer.get("free_form_answer") or "").strip()
    return [free_form] if free_form else []


def _dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _extract_metadata(raw_paper: dict[str, Any]) -> dict[str, Any]:
    metadata_keys = (
        "arxiv_id",
        "arxiv",
        "acl_id",
        "acl_anthology_id",
        "semantic_scholar_id",
        "s2_paper_id",
        "doi",
        "url",
        "paper_url",
        "pdf_url",
    )
    metadata = {key: raw_paper[key] for key in metadata_keys if raw_paper.get(key)}
    for key in ("id", "title"):
        if raw_paper.get(key):
            metadata[key] = raw_paper[key]
    return metadata


def generate_fallback_pdf(document: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text_lines = _document_lines(document)
    pages = _paginate(text_lines, lines_per_page=54)
    output_path.write_bytes(_build_pdf_bytes(pages))


def _document_lines(document: dict[str, Any]) -> list[str]:
    lines = [
        PDF_PROVENANCE_TEXT,
        f"QASPER doc_id: {document['doc_id']}",
        f"Title: {document.get('title', '')}",
        "",
        "Abstract",
    ]
    lines.extend(_wrap_text(str(document.get("abstract") or "")))
    for section in document.get("sections") or []:
        lines.append("")
        lines.append(str(section.get("section_name") or "Untitled Section"))
        for paragraph in section.get("paragraphs") or []:
            lines.extend(_wrap_text(str(paragraph)))
            lines.append("")
    return lines


def _wrap_text(text: str, width: int = 92) -> list[str]:
    if not text.strip():
        return [""]
    return textwrap.wrap(text, width=width, replace_whitespace=True, drop_whitespace=True)


def _paginate(lines: list[str], lines_per_page: int) -> list[list[str]]:
    return [lines[index : index + lines_per_page] for index in range(0, len(lines), lines_per_page)] or [[]]


def _build_pdf_bytes(pages: list[list[str]]) -> bytes:
    objects: list[bytes] = []

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []

    for page_lines in pages:
        stream = _page_stream(page_lines)
        stream_id = add_object(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {stream_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
    assert catalog_id == 1

    content = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, payload in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(payload)
        content.extend(b"\nendobj\n")
    xref_at = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(content)


def _page_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 10 Tf", "13 TL", "50 760 Td"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _pdf_escape(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_manifest_entry(
    *,
    document: dict[str, Any],
    qa_rows: list[dict[str, Any]],
    pdf_path: Path,
    pdf_type: PdfType,
    pdf_source_url: str | None,
    qasper_source: str,
    licence: str,
    download_status: str,
    notes: str,
) -> dict[str, Any]:
    related_rows = [row for row in qa_rows if row["doc_id"] == document["doc_id"]]
    if pdf_type == "generated" and PDF_PROVENANCE_TEXT not in notes:
        notes = f"{PDF_PROVENANCE_TEXT} {notes}".strip()
    return {
        "doc_id": document["doc_id"],
        "split": document["split"],
        "title": document.get("title", ""),
        "pdf_path": pdf_path.as_posix(),
        "pdf_type": pdf_type,
        "pdf_source_url": pdf_source_url,
        "qasper_source": qasper_source,
        "licence": licence,
        "sha256": sha256_file(pdf_path),
        "content_hash": content_hash_for_document(document),
        "has_questions": bool(related_rows),
        "num_questions": len(related_rows),
        "num_answers": sum(len(row.get("annotations") or []) for row in related_rows),
        "num_gold_evidence_items": sum(len(row.get("gold_evidence") or []) for row in related_rows),
        "download_status": download_status,
        "notes": notes,
    }


def load_qasper_dataset(cache_dir: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("Install the 'datasets' package to download allenai/qasper.") from exc

    dataset = load_dataset(QASPER_DATASET_NAME, cache_dir=str(cache_dir) if cache_dir else None)
    return {split: [dict(row) for row in dataset[split]] for split in ("train", "validation", "test")}


def write_raw_splits(splits: dict[str, list[dict[str, Any]]], paths: Step00Paths) -> dict[str, Any]:
    timestamp = dt.datetime.now(dt.UTC).isoformat()
    raw_files = []
    for split, rows in splits.items():
        path = paths.raw_qasper_dir / f"{split}.jsonl"
        _write_jsonl(path, rows)
        raw_files.append(
            {
                "split": split,
                "path": path.as_posix(),
                "sha256": sha256_file(path),
                "num_documents": len(rows),
            }
        )
    metadata = {
        "download_timestamp": timestamp,
        "source_url": QASPER_HF_URL,
        "dataset_name": QASPER_DATASET_NAME,
        "dataset_version": "huggingface/default",
        "licence": QASPER_LICENSE,
        "raw_files": raw_files,
    }
    metadata_path = paths.raw_qasper_dir / "download_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def run_step00(
    *,
    paths: Step00Paths,
    download_original_pdfs: bool = True,
    rate_limit_seconds: float = 1.0,
    min_usable_pdfs: int = 1000,
) -> dict[str, Any]:
    paths.ensure()
    splits = load_qasper_dataset(cache_dir=paths.raw_qasper_dir / "hf_cache")
    raw_metadata = write_raw_splits(splits, paths)

    documents: list[dict[str, Any]] = []
    qa_rows: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for split, papers in splits.items():
        for raw_paper in papers:
            document, document_qa_rows = normalize_document(raw_paper, split)
            documents.append(document)
            qa_rows.extend(document_qa_rows)

            resolution = (
                resolve_and_download_pdf(document, paths.original_pdf_dir, rate_limit_seconds)
                if download_original_pdfs
                else PdfResolution(False, None, None, "original PDF download disabled")
            )
            if resolution.success and resolution.path is not None:
                pdf_path = resolution.path
                pdf_type: PdfType = "original"
                status = "success"
                notes = "Original open-access PDF downloaded."
            else:
                pdf_path = paths.generated_pdf_dir / f"{_safe_filename(document['doc_id'])}.pdf"
                generate_fallback_pdf(document, pdf_path)
                pdf_type = "generated"
                status = "generated"
                notes = PDF_PROVENANCE_TEXT
                failures.append(
                    {
                        "doc_id": document["doc_id"],
                        "split": split,
                        "title": document.get("title", ""),
                        "reason": resolution.reason,
                        "attempted_url": resolution.url,
                    }
                )

            manifest_entries.append(
                build_manifest_entry(
                    document=document,
                    qa_rows=document_qa_rows,
                    pdf_path=pdf_path,
                    pdf_type=pdf_type,
                    pdf_source_url=resolution.url if pdf_type == "original" else None,
                    qasper_source=QASPER_HF_URL,
                    licence=QASPER_LICENSE,
                    download_status=status,
                    notes=notes,
                )
            )

    _write_jsonl(paths.processed_documents_path, documents)
    _write_jsonl(paths.processed_qa_path, qa_rows)
    _write_jsonl(paths.eval_qa_path, qa_rows)
    _write_jsonl(paths.failures_path, failures)
    paths.manifest_path.write_text(
        json.dumps(
            {
                "created_at": dt.datetime.now(dt.UTC).isoformat(),
                "qasper": raw_metadata,
                "documents": manifest_entries,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    summary = validate_outputs(paths, min_usable_pdfs=min_usable_pdfs)
    write_summary_reports(summary, paths)
    return summary


@dataclass(frozen=True)
class PdfResolution:
    success: bool
    path: Path | None
    url: str | None
    reason: str


def resolve_and_download_pdf(
    document: dict[str, Any],
    output_dir: Path,
    rate_limit_seconds: float,
) -> PdfResolution:
    candidates = pdf_candidate_urls(document)
    if not candidates:
        return PdfResolution(False, None, None, "no supported PDF identifiers in QASPER metadata")

    for url in candidates:
        time.sleep(rate_limit_seconds)
        path = output_dir / f"{_safe_filename(document['doc_id'])}.pdf"
        try:
            if _download_pdf(url, path):
                return PdfResolution(True, path, url, "downloaded")
        except Exception as exc:  # network failures are recorded and followed by generated fallback
            last_reason = f"{type(exc).__name__}: {exc}"
        else:
            last_reason = "URL did not return a PDF"
    return PdfResolution(False, None, candidates[-1], last_reason)


def pdf_candidate_urls(document: dict[str, Any]) -> list[str]:
    metadata = document.get("metadata") or {}
    candidates: list[str] = []
    for key in ("pdf_url", "url", "paper_url"):
        url = metadata.get(key)
        if isinstance(url, str) and url.lower().endswith(".pdf"):
            candidates.append(url)

    arxiv_id = metadata.get("arxiv_id") or metadata.get("arxiv") or _find_arxiv_id(metadata)
    if arxiv_id:
        candidates.append(f"https://arxiv.org/pdf/{_clean_arxiv_id(str(arxiv_id))}.pdf")

    acl_id = metadata.get("acl_id") or metadata.get("acl_anthology_id")
    if acl_id:
        candidates.append(f"https://aclanthology.org/{str(acl_id).strip()}.pdf")

    doi = metadata.get("doi")
    if doi:
        candidates.extend(_open_access_urls_for_doi(str(doi)))

    return _dedupe_preserving_order(candidates)


def _open_access_urls_for_doi(doi: str) -> list[str]:
    urls: list[str] = []
    try:
        import requests

        openalex = requests.get(f"https://api.openalex.org/works/doi:{doi}", timeout=20)
        if openalex.ok:
            data = openalex.json()
            open_access = data.get("open_access") or {}
            for key in ("oa_url", "any_repository_has_fulltext"):
                value = open_access.get(key)
                if isinstance(value, str) and value.lower().endswith(".pdf"):
                    urls.append(value)
            primary = data.get("primary_location") or {}
            pdf_url = primary.get("pdf_url")
            if isinstance(pdf_url, str):
                urls.append(pdf_url)
        crossref = requests.get(f"https://api.crossref.org/works/{doi}", timeout=20)
        if crossref.ok:
            links = ((crossref.json().get("message") or {}).get("link") or [])
            for link in links:
                if link.get("content-type") == "application/pdf" and link.get("URL"):
                    urls.append(link["URL"])
    except Exception:
        return urls
    return urls


def _download_pdf(url: str, path: Path) -> bool:
    import requests

    response = requests.get(url, timeout=45, headers={"User-Agent": "ScalableRAG-Step00/1.0"})
    if not response.ok:
        return False
    content_type = response.headers.get("content-type", "").lower()
    payload = response.content
    if "pdf" not in content_type and not payload.startswith(b"%PDF"):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return True


def _find_arxiv_id(metadata: dict[str, Any]) -> str | None:
    text = " ".join(str(value) for value in metadata.values())
    match = re.search(r"(?:arxiv[:/ ]+)?(\d{4}\.\d{4,5}(?:v\d+)?)", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _clean_arxiv_id(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^arxiv[:/ ]+", "", value, flags=re.IGNORECASE)
    return value.removesuffix(".pdf")


def validate_outputs(paths: Step00Paths, min_usable_pdfs: int = 1000) -> dict[str, Any]:
    manifest_payload = json.loads(paths.manifest_path.read_text(encoding="utf-8"))
    documents = manifest_payload.get("documents") or []
    qa_rows = _read_jsonl(paths.eval_qa_path)
    manifest_doc_ids = {entry["doc_id"] for entry in documents}
    errors: list[str] = []

    original_count = 0
    generated_count = 0
    for entry in documents:
        pdf_path = Path(entry["pdf_path"])
        if not pdf_path.is_absolute():
            pdf_path = paths.root / pdf_path
        if not pdf_path.exists():
            errors.append(f"PDF path does not exist for {entry['doc_id']}: {entry['pdf_path']}")
        if not entry.get("sha256"):
            errors.append(f"Missing checksum for {entry['doc_id']}")
        if entry.get("pdf_type") == "generated":
            generated_count += 1
            if PDF_PROVENANCE_TEXT not in str(entry.get("notes", "")):
                errors.append(f"Generated PDF missing provenance note for {entry['doc_id']}")
        elif entry.get("pdf_type") == "original":
            original_count += 1
            if not entry.get("pdf_source_url"):
                errors.append(f"Original PDF missing source URL for {entry['doc_id']}")
        else:
            errors.append(f"Invalid pdf_type for {entry['doc_id']}: {entry.get('pdf_type')}")

    for row in qa_rows:
        if row["doc_id"] not in manifest_doc_ids:
            errors.append(f"QA row maps to missing doc_id: {row['query_id']} -> {row['doc_id']}")

    usable_pdfs = len(documents) - sum(1 for error in errors if error.startswith("PDF path does not exist"))
    if usable_pdfs < min_usable_pdfs:
        errors.append(f"Only {usable_pdfs} usable PDFs; required at least {min_usable_pdfs}")

    total_answers = sum(int(entry.get("num_answers") or 0) for entry in documents)
    total_evidence = sum(int(entry.get("num_gold_evidence_items") or 0) for entry in documents)
    return {
        "total_qasper_documents": len(documents),
        "total_usable_pdfs": usable_pdfs,
        "original_pdfs_downloaded": original_count,
        "fallback_pdfs_generated": generated_count,
        "failed_documents": len(_read_jsonl(paths.failures_path)) if paths.failures_path.exists() else 0,
        "total_questions": len(qa_rows),
        "total_answer_annotations": total_answers,
        "total_evidence_annotations": total_evidence,
        "licence_summary": {QASPER_LICENSE: len(documents)},
        "caveats": [
            "QASPER does not provide original PDFs for every paper.",
            "Generated PDFs are marked as generated and should not be treated as original publisher PDFs.",
            "Original PDF resolution is limited to legally accessible open PDF URLs from available identifiers and open metadata.",
        ],
        "validation_errors": errors,
    }


def write_summary_reports(summary: dict[str, Any], paths: Step00Paths) -> None:
    paths.summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Step 00 Dataset Summary",
        "",
        f"- Total QASPER documents: {summary['total_qasper_documents']}",
        f"- Total usable PDFs: {summary['total_usable_pdfs']}",
        f"- Original PDFs downloaded: {summary['original_pdfs_downloaded']}",
        f"- Fallback PDFs generated: {summary['fallback_pdfs_generated']}",
        f"- Failed documents: {summary['failed_documents']}",
        f"- Total questions: {summary['total_questions']}",
        f"- Total answer annotations: {summary['total_answer_annotations']}",
        f"- Total evidence annotations: {summary['total_evidence_annotations']}",
        f"- Licence summary: {json.dumps(summary['licence_summary'], sort_keys=True)}",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {caveat}" for caveat in summary["caveats"])
    lines.extend(["", "## Validation", ""])
    if summary["validation_errors"]:
        lines.extend(f"- {error}" for error in summary["validation_errors"])
    else:
        lines.append("- No validation errors.")
    paths.summary_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return safe or hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 00: prepare QASPER PDFs and evaluation ground truth.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--skip-original-pdf-downloads", action="store_true")
    parser.add_argument("--rate-limit-seconds", type=float, default=1.0)
    parser.add_argument("--min-usable-pdfs", type=int, default=1000)
    args = parser.parse_args()

    summary = run_step00(
        paths=Step00Paths(root=args.root),
        download_original_pdfs=not args.skip_original_pdf_downloads,
        rate_limit_seconds=args.rate_limit_seconds,
        min_usable_pdfs=args.min_usable_pdfs,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
