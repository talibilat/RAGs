CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(512) NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    tenant_id VARCHAR(128) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_documents_tenant_hash UNIQUE (tenant_id, sha256_hash)
);

CREATE INDEX IF NOT EXISTS ix_documents_tenant_id ON documents (tenant_id);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_status') THEN
        CREATE TYPE document_status AS ENUM (
            'pending',
            'parsing',
            'parsed',
            'chunking',
            'indexed',
            'failed'
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS document_versions (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE RESTRICT,
    version_hash CHAR(64) NOT NULL,
    status document_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_document_versions_document_id
    ON document_versions (document_id);
