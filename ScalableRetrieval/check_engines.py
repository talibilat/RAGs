import asyncio
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient

def check_opensearch():
    print("\n--- OpenSearch Content ---")
    os_client = OpenSearch([{"host": "localhost", "port": 9200}], http_auth=("admin", "admin"), use_ssl=False)
    try:
        if not os_client.indices.exists(index="rag_chunks"):
            print("Index 'rag_chunks' does not exist in OpenSearch.")
            return
        
        res = os_client.search(index="rag_chunks", body={"query": {"match_all": {}}})
        hits = res["hits"]["hits"]
        print(f"Found {len(hits)} items in OpenSearch:")
        for hit in hits:
            print(f" - ID: {hit['_id']}, Tenant: {hit['_source'].get('tenant_id')}, Text: {hit['_source'].get('text')[:50]}...")
    except Exception as e:
        print(f"Error checking OpenSearch: {e}")
    finally:
        os_client.close()

def check_qdrant():
    print("\n--- Qdrant Content ---")
    q_client = QdrantClient("localhost", port=6333)
    try:
        if not q_client.collection_exists("rag_chunks"):
            print("Collection 'rag_chunks' does not exist in Qdrant.")
            return
            
        res = q_client.scroll(collection_name="rag_chunks", limit=10, with_payload=True)
        points = res[0]
        print(f"Found {len(points)} items in Qdrant:")
        for point in points:
            print(f" - ID: {point.id}, Tenant: {point.payload.get('tenant_id')}, Text: {point.payload.get('text')[:50]}...")
    except Exception as e:
        print(f"Error checking Qdrant: {e}")

if __name__ == "__main__":
    check_opensearch()
    check_qdrant()
