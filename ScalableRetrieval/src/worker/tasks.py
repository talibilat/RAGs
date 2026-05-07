import logging
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from src.retrieval.dual_engine import _get_or_create_os_index

logger = logging.getLogger(__name__)


async def process_document(ctx, document_id: str, tenant_id: str = "default"):
    """
    Entry-point task for document processing.

    A caller can provide `ctx["process_document_pipeline"]` to run the full
    parse/chunk/embed enqueue pipeline. Without that injectable pipeline, the
    task returns an acknowledgement so ARQ queue wiring remains testable in
    local CI without Azure credentials.
    """
    logger.info("process_document started: doc=%s tenant=%s", document_id, tenant_id)
    if "process_document_pipeline" in ctx:
        return await ctx["process_document_pipeline"](document_id, tenant_id)
    return {"status": "processing", "document_id": document_id, "tenant_id": tenant_id}


async def embed_chunks(ctx, chunk_ids: list[str], tenant_id: str = "default"):
    """
    Embedding task for chunk batches.

    A caller can provide `ctx["embed_chunks_pipeline"]` to call Azure OpenAI,
    persist vectors, and enqueue sync work. Without that injectable pipeline,
    the task returns an acknowledgement so queue registration is testable
    without cloud credentials.
    """
    logger.info("embed_chunks started: %d chunks, tenant=%s", len(chunk_ids), tenant_id)
    if "embed_chunks_pipeline" in ctx:
        return await ctx["embed_chunks_pipeline"](chunk_ids, tenant_id)
    return {"status": "embedded", "chunks_count": len(chunk_ids), "tenant_id": tenant_id}


async def sync_to_search_engines(ctx, chunks: list[dict], tenant_id: str = "default"):
    """
    Idempotent outbox-style sync.  Reads fully-formed chunk dicts
    (chunk_id, text, vector, tenant_id) and upserts them into both
    OpenSearch and Qdrant.  Safe to retry — both operations are upserts.

    Each chunk dict must contain:
        chunk_id  : str  (UUID)
        text      : str
        vector    : list[float]
        tenant_id : str  (optional; falls back to the task-level tenant_id)
    """
    if not chunks:
        return {"status": "synced", "chunks_count": 0}

    # ── OpenSearch ────────────────────────────────────────────────────────────
    os_client = OpenSearch(
        [{"host": "localhost", "port": 9200}],
        http_auth=("admin", "admin"),
        use_ssl=False,
    )
    _get_or_create_os_index(os_client, index="rag_chunks")

    for chunk in chunks:
        effective_tenant = chunk.get("tenant_id", tenant_id)
        os_client.index(
            index="rag_chunks",
            id=chunk["chunk_id"],
            body={
                "text": chunk["text"],
                "tenant_id": effective_tenant,
                "doc_id": chunk.get("doc_id"),
                "document_version_id": chunk.get("document_version_id"),
                "structural_path": chunk.get("structural_path", ""),
            },
        )
        logger.info("OpenSearch upsert: chunk=%s tenant=%s", chunk["chunk_id"], effective_tenant)

    # ── Qdrant ────────────────────────────────────────────────────────────────
    q_client = QdrantClient("localhost", port=6333)
    vector_size = len(chunks[0]["vector"])

    if not q_client.collection_exists("rag_chunks"):
        q_client.create_collection(
            collection_name="rag_chunks",
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    points = [
        PointStruct(
            id=chunk["chunk_id"],
            vector=chunk["vector"],
            payload={
                "text": chunk["text"],
                "tenant_id": chunk.get("tenant_id", tenant_id),
                "doc_id": chunk.get("doc_id"),
                "document_version_id": chunk.get("document_version_id"),
                "structural_path": chunk.get("structural_path", ""),
            },
        )
        for chunk in chunks
    ]
    q_client.upsert(collection_name="rag_chunks", points=points)
    logger.info("Qdrant upsert: %d points, tenant=%s", len(points), tenant_id)

    return {"status": "synced", "chunks_count": len(chunks)}
