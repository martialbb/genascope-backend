-- Initialize pgvector extension for Genascope
-- This script creates the vector extension for AI/ML capabilities

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify the extension was created
SELECT 'pgvector extension initialized successfully' as status, 
       extname, extversion 
FROM pg_extension 
WHERE extname = 'vector';

-- Log the pgvector initialization
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension initialized for Genascope database';
END $$;
