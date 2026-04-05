-- Railway PostgreSQL Schema for AntiGravity BAM
-- No auth dependencies - fully public API

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS clients (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    brand       TEXT NOT NULL,
    config_json JSONB NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id        UUID REFERENCES clients(id) ON DELETE CASCADE,
    status           TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed')) DEFAULT 'pending',
    total_messages   INT,
    total_bigrams    INT,
    tagged_pct       FLOAT,
    run_duration_sec FLOAT,
    error_message    TEXT,
    created_at       TIMESTAMPTZ DEFAULT now(),
    completed_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS results_data (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    level           TEXT CHECK (level IN ('word', 't2', 't3', 't4')),
    attribute_t1    TEXT,
    attribute_t2    TEXT,
    attribute_t3    TEXT,
    attribute_t4    TEXT,
    word1           TEXT,
    word2           TEXT,
    mentions        INT,
    positive        INT,
    negative        INT,
    total           INT,
    positive_pct    FLOAT,
    negative_pct    FLOAT,
    mentions_assoc  TEXT,
    sentiment_assoc TEXT,
    overall_assoc   TEXT
);

CREATE TABLE IF NOT EXISTS taxonomy_suggestions (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id       UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    word1        TEXT,
    word2        TEXT,
    suggested_t1 TEXT,
    suggested_t2 TEXT,
    suggested_t3 TEXT,
    suggested_t4 TEXT,
    status       TEXT CHECK (status IN ('pending', 'approved', 'rejected', 'edited')) DEFAULT 'pending',
    analyst_notes TEXT,
    reviewed_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS feedback (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id        UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    category      TEXT CHECK (category IN ('accuracy', 'completeness', 'usefulness', 'general')),
    rating        INT CHECK (rating BETWEEN 1 AND 5),
    comment       TEXT,
    attribute_ref TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_results_run_id ON results_data(run_id);
CREATE INDEX IF NOT EXISTS idx_results_level ON results_data(level);
CREATE INDEX IF NOT EXISTS idx_runs_client_id ON pipeline_runs(client_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_run_id ON taxonomy_suggestions(run_id);
CREATE INDEX IF NOT EXISTS idx_feedback_run_id ON feedback(run_id);
