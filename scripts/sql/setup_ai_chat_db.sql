-- Setup script for AI Chat tables in PostgreSQL with pgvector
-- This creates the minimal required schema for AI chat functionality

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create basic accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create basic users table  
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create basic patients table
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create knowledge sources table
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat strategies table
CREATE TABLE IF NOT EXISTS chat_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    specialty VARCHAR(100),
    goal TEXT,
    patient_introduction TEXT,
    ai_model_config JSON,
    targeting_rules JSON,
    outcome_actions JSON,
    extraction_rules JSON,
    assessment_criteria JSON,
    required_information JSON,
    max_conversation_turns INTEGER DEFAULT 20,
    rag_enabled BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create enums for AI chat
CREATE TYPE session_type AS ENUM ('screening', 'assessment', 'follow_up', 'consultation');
CREATE TYPE session_status AS ENUM ('active', 'completed', 'paused', 'error', 'cancelled');
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE message_type AS ENUM ('question', 'response', 'summary', 'assessment', 'clarification');
CREATE TYPE extraction_method AS ENUM ('llm', 'regex', 'ner', 'hybrid');

-- Create chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES chat_strategies(id),
    patient_id UUID REFERENCES patients(id),
    session_type session_type NOT NULL,
    status session_status NOT NULL DEFAULT 'active',
    chat_context JSON,
    extracted_data JSON,
    assessment_results JSON,
    strategy_snapshot JSON,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    role message_role NOT NULL,
    content TEXT NOT NULL,
    message_type message_type NOT NULL,
    prompt_template TEXT,
    rag_sources JSON,
    confidence_score FLOAT,
    extracted_entities JSON,
    extracted_intent VARCHAR(100),
    processing_time_ms INTEGER,
    message_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create extraction rules table
CREATE TABLE IF NOT EXISTS extraction_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES chat_strategies(id),
    entity_type VARCHAR(100) NOT NULL,
    extraction_method extraction_method NOT NULL,
    pattern TEXT,
    validation_rules JSON,
    priority INTEGER DEFAULT 1,
    trigger_conditions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create session analytics table
CREATE TABLE IF NOT EXISTS session_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    total_messages INTEGER DEFAULT 0,
    conversation_duration_seconds INTEGER,
    completion_rate FLOAT,
    extraction_accuracy FLOAT,
    patient_satisfaction_score FLOAT,
    ai_confidence_avg FLOAT,
    criteria_met BOOLEAN,
    recommendations_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create document chunks table with pgvector
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_source_id UUID REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 embedding size
    chunk_index INTEGER NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS ix_chat_sessions_strategy_id ON chat_sessions(strategy_id);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_patient_id ON chat_sessions(patient_id);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_status ON chat_sessions(status);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_created_at ON chat_sessions(created_at);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS ix_chat_messages_role ON chat_messages(role);
CREATE INDEX IF NOT EXISTS ix_chat_messages_created_at ON chat_messages(created_at);

CREATE INDEX IF NOT EXISTS ix_document_chunks_knowledge_source ON document_chunks(knowledge_source_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_created_at ON document_chunks(created_at);
CREATE INDEX IF NOT EXISTS ix_document_chunks_chunk_index ON document_chunks(chunk_index);

-- Create full-text search index
CREATE INDEX IF NOT EXISTS ix_document_chunks_content_fts 
ON document_chunks USING gin (to_tsvector('english', content));

-- Create vector similarity index (ivfflat for cosine similarity)
CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_cosine 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_sources_updated_at BEFORE UPDATE ON knowledge_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_strategies_updated_at BEFORE UPDATE ON chat_strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_rules_updated_at BEFORE UPDATE ON extraction_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_analytics_updated_at BEFORE UPDATE ON session_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_chunks_updated_at BEFORE UPDATE ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO accounts (id, name) VALUES 
    ('550e8400-e29b-41d4-a716-446655440000', 'Demo Healthcare Org')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, account_id, name, email, role) VALUES 
    ('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', 'Dr. Demo', 'demo@genascope.com', 'admin')
ON CONFLICT (email) DO NOTHING;

INSERT INTO patients (id, account_id, name, email) VALUES 
    ('770e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', 'Jane Doe', 'jane.doe@example.com')
ON CONFLICT DO NOTHING;

-- Sample chat strategy for breast cancer screening
INSERT INTO chat_strategies (
    id, 
    account_id, 
    name, 
    description, 
    specialty, 
    goal,
    patient_introduction,
    ai_model_config,
    targeting_rules,
    outcome_actions,
    extraction_rules,
    assessment_criteria,
    required_information
) VALUES (
    '880e8400-e29b-41d4-a716-446655440003',
    '550e8400-e29b-41d4-a716-446655440000',
    'Breast Cancer Risk Assessment',
    'AI-driven conversation to assess breast cancer risk and determine genetic testing eligibility',
    'Oncology',
    'Assess breast cancer risk through structured conversation and determine if genetic testing is recommended',
    'I''ll help you assess your breast cancer risk through a brief conversation about your personal and family medical history.',
    '{"model": "gpt-4", "temperature": 0.7, "max_tokens": 500}',
    '[]',
    '[{"condition": "high_risk", "action": "recommend_genetic_testing"}]',
    '[{"entity": "age", "method": "llm", "pattern": "extract age from patient response"}]',
    '[{"criteria": "family_history_positive", "weight": 0.4}]',
    '["age", "family_history", "personal_history", "previous_testing"]'
) ON CONFLICT (id) DO NOTHING;

COMMIT;
