import argparse
import hashlib
import uuid
from pathlib import Path

from sqlalchemy import select
from tqdm import tqdm

from src.config.settings import settings
from src.ingestion.chunker import MarkdownChunker
from src.ingestion.embedding import AzureEmbeddingClient, ZeroWasteEmbedder
from src.ledger.models import ChunkEmbedding, Document, DocumentVersion
from src.parsing.parse import build_session_factory_from_url
from src.worker.tasks import sync_to_search_engines


def get_version_id_by_doc_id(session_factory, doc_id: str) -> int:
    with session_factory() as session:
        version = session.scalar(
            select(DocumentVersion)
            .join(Document)
            .where(Document.id == int(doc_id))
            .order_by(DocumentVersion.id.desc())
            .limit(1)
        )
        if version is None:
            raise ValueError(f"No version found for doc_id {doc_id}")
        return version.id


def document_version_has_chunks(session_factory, version_id: int) -> bool:
    with session_factory() as session:
        existing_chunk = session.scalar(
            select(ChunkEmbedding.id)
            .where(ChunkEmbedding.document_version_id == version_id)
            .limit(1)
        )
        return existing_chunk is not None


def get_source_doc_id_by_version_id(session_factory, version_id: int) -> str:
    with session_factory() as session:
        document = session.scalar(
            select(Document)
            .join(DocumentVersion)
            .where(DocumentVersion.id == version_id)
            .limit(1)
        )
        if document is None:
            raise ValueError(f"No document found for version_id {version_id}")
        return Path(document.filename).stem


def get_chunks_for_version(session_factory, version_id: int) -> list[ChunkEmbedding]:
    with session_factory() as session:
        return list(
            session.scalars(
                select(ChunkEmbedding).where(ChunkEmbedding.document_version_id == version_id)
            ).all()
        )


def build_search_chunk_id(document_version_id: int, chunk_hash: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_version_id}:{chunk_hash}"))


def build_sync_data(
    chunks: list[ChunkEmbedding],
    *,
    source_doc_id: str,
    tenant_id: str = "qasper_eval",
) -> list[dict]:
    return [
        {
            "chunk_id": build_search_chunk_id(c.document_version_id, c.chunk_hash),
            "chunk_hash": c.chunk_hash,
            "text": c.text_content,
            "vector": c.embedding,
            "tenant_id": tenant_id,
            "doc_id": source_doc_id,
            "document_version_id": c.document_version_id,
            "structural_path": c.structural_path,
        }
        for c in chunks
    ]


def run_step03(
    parsed_dir: Path,
    database_url: str = settings.postgres_dsn,
    strategy: str = "section_aware",
):
    session_factory = build_session_factory_from_url(database_url)
    chunker = MarkdownChunker(strategy=strategy)
    embed_client = AzureEmbeddingClient(
        endpoint=settings.AZURE_OPENAI_ENDPOINT or "",
        key=settings.AZURE_OPENAI_KEY or "",
        deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )
    embedder = ZeroWasteEmbedder(embed_client, session_factory)

    markdown_files = list(parsed_dir.glob("*.md"))
    tqdm.write(f"Indexing {len(markdown_files)} markdown files using {strategy} strategy...")

    progress = tqdm(
        markdown_files,
        total=len(markdown_files),
        desc="Indexing markdown",
        unit="doc",
        dynamic_ncols=True,
    )
    for md_file in progress:
        doc_id = md_file.stem
        if hasattr(progress, "set_postfix"):
            progress.set_postfix({"doc": doc_id})
        try:
            version_id = get_version_id_by_doc_id(session_factory, doc_id)
        except ValueError as e:
            tqdm.write(f"Skipping {md_file.name}: {e}")
            continue
        source_doc_id = get_source_doc_id_by_version_id(session_factory, version_id)
        if document_version_has_chunks(session_factory, version_id):
            tqdm.write(f"Re-syncing {doc_id}: chunks already exist in ledger.")
            chunks = []
        else:
            text = md_file.read_text(encoding="utf-8")
            chunks = chunker.chunk_document(text, version_id, tenant_id="qasper_eval")
            embedder.embed_and_store(chunks)

        # Retrieve the chunks with embeddings from the ledger to sync to search engines
        db_chunks = get_chunks_for_version(session_factory, version_id)
        sync_data = build_sync_data(db_chunks, source_doc_id=source_doc_id)

        # Sync to search engines (OpenSearch + Qdrant)
        # sync_to_search_engines is async, so we run it via asyncio
        import asyncio
        asyncio.run(sync_to_search_engines({}, sync_data, tenant_id="qasper_eval"))
        
        if hasattr(progress, "set_postfix"):
            progress.set_postfix({"doc": doc_id, "chunks": len(chunks)})
        tqdm.write(f"Indexed {doc_id}: {len(chunks)} chunks.")


def main():
    parser = argparse.ArgumentParser(description="QASPER Step 03: Chunk and Index.")
    parser.add_argument("--parsed-dir", type=Path, default=Path("data/processed/pdf_text"))
    parser.add_argument("--strategy", default="section_aware")
    args = parser.parse_args()

    run_step03(parsed_dir=args.parsed_dir, strategy=args.strategy)


if __name__ == "__main__":
    main()
