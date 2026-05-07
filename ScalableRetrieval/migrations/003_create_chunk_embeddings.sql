CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    id BIGSERIAL PRIMARY KEY,
    chunk_hash CHAR(64) NOT NULL,
    document_version_id BIGINT NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
    text_content TEXT NOT NULL,
    structural_path VARCHAR(512) NOT NULL,
    embedding VECTOR(3072) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_chunk_embeddings_chunk_hash ON chunk_embeddings (chunk_hash);
CREATE INDEX IF NOT EXISTS ix_chunk_embeddings_document_version_id ON chunk_embeddings (document_version_id);
