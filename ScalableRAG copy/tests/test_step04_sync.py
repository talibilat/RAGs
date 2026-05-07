import pytest
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
from src.worker.tasks import sync_to_search_engines

CHUNK_1_ID = "11111111-1111-1111-1111-111111111111"
CHUNK_2_ID = "22222222-2222-2222-2222-222222222222"
TENANT = "tenant_integration_test"


@pytest.mark.asyncio
async def test_sync_upserts_to_opensearch_with_tenant():
    chunks = [
        {"chunk_id": CHUNK_1_ID, "text": "This is a test chunk", "vector": [0.1, 0.2, 0.3, 0.4], "tenant_id": TENANT},
    ]
    result = await sync_to_search_engines({}, chunks, tenant_id=TENANT)
    assert result["status"] == "synced"

    os_client = OpenSearch([{"host": "localhost", "port": 9200}], http_auth=("admin", "admin"), use_ssl=False)
    doc = os_client.get(index="rag_chunks", id=CHUNK_1_ID)
    assert doc["_source"]["text"] == "This is a test chunk"
    # Critical Plan 04 gap fix: tenant_id must be stored for Plan 05 ACL filters
    assert doc["_source"]["tenant_id"] == TENANT

    mapping = os_client.indices.get_mapping(index="rag_chunks")
    assert mapping["rag_chunks"]["mappings"]["properties"]["tenant_id"]["type"] == "keyword"


@pytest.mark.asyncio
async def test_sync_upserts_to_qdrant_with_tenant():
    chunks = [
        {"chunk_id": CHUNK_2_ID, "text": "Another test chunk", "vector": [0.5, 0.6, 0.7, 0.8], "tenant_id": TENANT},
    ]
    result = await sync_to_search_engines({}, chunks, tenant_id=TENANT)
    assert result["status"] == "synced"

    qdrant_client = QdrantClient("localhost", port=6333)
    res = qdrant_client.retrieve("rag_chunks", ids=[CHUNK_2_ID], with_vectors=True, with_payload=True)
    assert len(res) == 1
    assert res[0].id == CHUNK_2_ID
    assert len(res[0].vector) == 4
    # Critical Plan 04 gap fix: tenant_id must be in payload for Plan 05 ACL filters
    assert res[0].payload["tenant_id"] == TENANT
