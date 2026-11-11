CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_vault (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    stream_type TEXT NOT NULL
        CHECK (stream_type IN ('framework', 'voice_sample')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1024) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT knowledge_vault_session_stream_content_unique
        UNIQUE (session_id, stream_type, content)
);

CREATE INDEX IF NOT EXISTS knowledge_vault_embedding_hnsw
ON knowledge_vault
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS knowledge_vault_session_idx
ON knowledge_vault (session_id);

CREATE INDEX IF NOT EXISTS knowledge_vault_stream_idx
ON knowledge_vault (stream_type);

CREATE TABLE IF NOT EXISTS archived_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    meeting_type TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    summary TEXT,
    transcript JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    rejection_reason TEXT,
    archived_at TIMESTAMPTZ DEFAULT NOW()
);
