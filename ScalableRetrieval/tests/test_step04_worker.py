import pytest
from src.worker.tasks import process_document, embed_chunks, sync_to_search_engines


@pytest.mark.asyncio
async def test_process_document_returns_ack():
    result = await process_document({}, "doc_123", tenant_id="tenant_a")
    assert result["status"] == "processing"
    assert result["document_id"] == "doc_123"
    assert result["tenant_id"] == "tenant_a"


@pytest.mark.asyncio
async def test_embed_chunks_returns_count():
    result = await embed_chunks({}, ["chunk_1", "chunk_2"], tenant_id="tenant_a")
    assert result["status"] == "embedded"
    assert result["chunks_count"] == 2
    assert result["tenant_id"] == "tenant_a"


@pytest.mark.asyncio
async def test_sync_to_search_engines_upserts_chunks():
    chunks = [
        {
            "chunk_id": "33333333-3333-3333-3333-333333333333",
            "text": "test chunk alpha",
            "vector": [0.1, 0.2, 0.3, 0.4],
            "tenant_id": "tenant_a",
        },
        {
            "chunk_id": "44444444-4444-4444-4444-444444444444",
            "text": "test chunk beta",
            "vector": [0.5, 0.6, 0.7, 0.8],
            "tenant_id": "tenant_a",
        },
    ]
    result = await sync_to_search_engines({}, chunks, tenant_id="tenant_a")
    assert result == {"status": "synced", "chunks_count": 2}


@pytest.mark.asyncio
async def test_sync_empty_chunks_is_noop():
    result = await sync_to_search_engines({}, [], tenant_id="tenant_a")
    assert result == {"status": "synced", "chunks_count": 0}


def test_arq_worker_settings_registers_all_tasks():
    from src.worker.main import WorkerSettings
    assert process_document in WorkerSettings.functions
    assert embed_chunks in WorkerSettings.functions
    assert sync_to_search_engines in WorkerSettings.functions
