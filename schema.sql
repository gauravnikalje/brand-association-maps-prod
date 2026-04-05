-- PostgreSQL Schema definition for AntiGravity BAM

-- 1. extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. clients table
-- Note: 'users' table is usually handled by auth.users in Supabase natively. 
-- We will assume standard Supabase auth.

CREATE TABLE IF NOT EXISTS public.clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    config_json JSONB NOT NULL,
    bigram_taxonomy_url TEXT,
    monogram_taxonomy_url TEXT,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. pipeline_runs
CREATE TABLE IF NOT EXISTS public.pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES public.clients(id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    input_file_url TEXT,
    output_file_url TEXT,
    results_json JSONB,
    total_messages INT,
    total_bigrams INT,
    tagged_pct FLOAT,
    run_duration_sec FLOAT,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- 4. results_data
CREATE TABLE IF NOT EXISTS public.results_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
    level TEXT CHECK (level IN ('word', 't2', 't3', 't4')),
    attribute_t1 TEXT,
    attribute_t2 TEXT,
    attribute_t3 TEXT,
    attribute_t4 TEXT,
    word1 TEXT,
    word2 TEXT,
    mentions INT,
    positive INT,
    negative INT,
    total INT,
    positive_pct FLOAT,
    negative_pct FLOAT,
    mentions_assoc TEXT,
    sentiment_assoc TEXT,
    overall_assoc TEXT
);

-- 5. taxonomy_suggestions
CREATE TABLE IF NOT EXISTS public.taxonomy_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
    word1 TEXT,
    word2 TEXT,
    suggested_t1 TEXT,
    suggested_t2 TEXT,
    suggested_t3 TEXT,
    suggested_t4 TEXT,
    status TEXT CHECK (status IN ('pending', 'approved', 'rejected', 'edited')),
    reviewed_by UUID REFERENCES auth.users(id),
    reviewed_at TIMESTAMPTZ,
    analyst_notes TEXT
);

-- 6. feedback
CREATE TABLE IF NOT EXISTS public.feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    category TEXT CHECK (category IN ('accuracy', 'completeness', 'usefulness', 'general')),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    attribute_ref TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Note: RLS (Row Level Security) policies should be added here depending on precise Lead vs Analyst access roles.
-- Setup storage buckets manually in the dashboard: "uploads", "outputs", "taxonomies"
