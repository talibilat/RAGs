import hashlib
from typing import List, Dict, Any
from sqlalchemy import select
from src.ledger.models import ChunkEmbedding

class AzureEmbeddingClient:
    def __init__(self, endpoint: str, key: str, deployment: str):
        from openai import AzureOpenAI
        from urllib.parse import urlparse
        
        # Sanitize endpoint: extract base URL if a full deployment URL was provided
        parsed = urlparse(endpoint)
        base_endpoint = f"{parsed.scheme}://{parsed.netloc}/"
        
        self.client = AzureOpenAI(
            api_key=key,
            api_version="2023-05-15",
            azure_endpoint=base_endpoint
        )
        self.deployment = deployment
        
    def embed_chunks(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(
            input=texts,
            model=self.deployment
        )
        # response.data is a list of Embedding objects, ordered by input
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


class ZeroWasteEmbedder:
    def __init__(self, client, session_factory):
        self.client = client
        self.session_factory = session_factory

    def embed_and_store(self, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            return
            
        # 1. Compute hashes
        for chunk in chunks:
            chunk_hash = hashlib.sha256(chunk["text_content"].encode('utf-8')).hexdigest()
            chunk["hash"] = chunk_hash

        hashes = [chunk["hash"] for chunk in chunks]
        
        with self.session_factory() as session:
            # 2. Check DB for existing hashes
            existing_chunks = session.scalars(
                select(ChunkEmbedding).where(ChunkEmbedding.chunk_hash.in_(hashes))
            ).all()
            
            # Create a map of hash -> vector
            cache = {c.chunk_hash: c.embedding for c in existing_chunks}
            
            # 3. Identify misses
            misses = []
            miss_indices = []
            for i, chunk in enumerate(chunks):
                if chunk["hash"] not in cache:
                    misses.append(chunk["text_content"])
                    miss_indices.append(i)
                    
            # 4. Embed misses
            if misses:
                new_embeddings = self.client.embed_chunks(misses)
                for miss_idx, embedding in zip(miss_indices, new_embeddings):
                    cache[chunks[miss_idx]["hash"]] = embedding
                    
            # 5. Store all chunks in ledger
            new_db_chunks = []
            for chunk in chunks:
                db_chunk = ChunkEmbedding(
                    chunk_hash=chunk["hash"],
                    document_version_id=chunk["document_version_id"],
                    text_content=chunk["text_content"],
                    structural_path=chunk["structural_path"],
                    embedding=cache[chunk["hash"]]
                )
                new_db_chunks.append(db_chunk)
                
            session.add_all(new_db_chunks)
            session.commit()
