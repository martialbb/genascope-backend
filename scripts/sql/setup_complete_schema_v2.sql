-- Complete GenaScope Database Schema for PostgreSQL
-- This script creates all the essential tables for the application

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Helper function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create ENUMs (drop first if they exist)
DROP TYPE IF EXISTS appointment_type CASCADE;
CREATE TYPE appointment_type AS ENUM ('virtual', 'in-person');

DROP TYPE IF EXISTS appointment_status CASCADE;
CREATE TYPE appointment_status AS ENUM ('scheduled', 'completed', 'canceled', 'rescheduled');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    account_id VARCHAR(36),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    clinician_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Clinician availability table
CREATE TABLE IF NOT EXISTS clinician_availability (
    id SERIAL PRIMARY KEY,
    clinician_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    time_slot VARCHAR(5) NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES patients(id) ON DELETE CASCADE,
    clinician_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    date_time TIMESTAMP NOT NULL,
    appointment_type appointment_type NOT NULL,
    status appointment_status NOT NULL,
    notes TEXT,
    confirmation_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) NOT NULL,
    patient_id VARCHAR(36) REFERENCES patients(id),
    clinician_id VARCHAR(36) REFERENCES users(id),
    session_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES chat_sessions(id) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Knowledge sources table
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    content_type VARCHAR(100),
    file_size INTEGER,
    processing_status VARCHAR(50) DEFAULT 'pending',
    uploaded_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Document chunks table for AI chat (pgvector)
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    knowledge_source_id VARCHAR(36) REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Chat strategies table
CREATE TABLE IF NOT EXISTS chat_strategies (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Extraction rules table
CREATE TABLE IF NOT EXISTS extraction_rules (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    pattern TEXT NOT NULL,
    extraction_method VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Session analytics table
CREATE TABLE IF NOT EXISTS session_analytics (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Invites table
CREATE TABLE IF NOT EXISTS invites (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(32),
    invite_token VARCHAR(64) NOT NULL,
    clinician_id VARCHAR(36) REFERENCES users(id),
    status VARCHAR(32),
    custom_message TEXT,
    session_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    accepted_at TIMESTAMP
);

-- Risk assessments table
CREATE TABLE IF NOT EXISTS risk_assessments (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES patients(id),
    assessment_type VARCHAR(100) NOT NULL,
    risk_score DECIMAL(5,2),
    risk_category VARCHAR(50),
    details JSONB,
    assessed_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Lab integration tables
CREATE TABLE IF NOT EXISTS lab_orders (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES patients(id),
    order_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    lab_reference VARCHAR(100),
    ordered_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS lab_results (
    id VARCHAR(36) PRIMARY KEY,
    lab_order_id VARCHAR(36) REFERENCES lab_orders(id),
    test_name VARCHAR(255) NOT NULL,
    result_value VARCHAR(255),
    unit VARCHAR(50),
    reference_range VARCHAR(100),
    status VARCHAR(50) DEFAULT 'final',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS eligibility_results (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES patients(id),
    eligibility_status VARCHAR(50) NOT NULL,
    criteria_met JSONB,
    assessed_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_document_chunks_knowledge_source ON document_chunks(knowledge_source_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_clinician ON appointments(clinician_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date_time);
CREATE INDEX IF NOT EXISTS idx_clinician_availability_date ON clinician_availability(clinician_id, date);
CREATE INDEX IF NOT EXISTS idx_invites_email ON invites(email);

-- Create triggers for automatic timestamp updates (drop first if they exist)
DROP TRIGGER IF EXISTS update_users_modtime ON users;
CREATE TRIGGER update_users_modtime
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_patients_modtime ON patients;
CREATE TRIGGER update_patients_modtime
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_chat_sessions_modtime ON chat_sessions;
CREATE TRIGGER update_chat_sessions_modtime
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_knowledge_sources_modtime ON knowledge_sources;
CREATE TRIGGER update_knowledge_sources_modtime
    BEFORE UPDATE ON knowledge_sources
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_chat_strategies_modtime ON chat_strategies;
CREATE TRIGGER update_chat_strategies_modtime
    BEFORE UPDATE ON chat_strategies
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_extraction_rules_modtime ON extraction_rules;
CREATE TRIGGER update_extraction_rules_modtime
    BEFORE UPDATE ON extraction_rules
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_accounts_modtime ON accounts;
CREATE TRIGGER update_accounts_modtime
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_invites_modtime ON invites;
CREATE TRIGGER update_invites_modtime
    BEFORE UPDATE ON invites
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_risk_assessments_modtime ON risk_assessments;
CREATE TRIGGER update_risk_assessments_modtime
    BEFORE UPDATE ON risk_assessments
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_lab_orders_modtime ON lab_orders;
CREATE TRIGGER update_lab_orders_modtime
    BEFORE UPDATE ON lab_orders
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_lab_results_modtime ON lab_results;
CREATE TRIGGER update_lab_results_modtime
    BEFORE UPDATE ON lab_results
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_eligibility_results_modtime ON eligibility_results;
CREATE TRIGGER update_eligibility_results_modtime
    BEFORE UPDATE ON eligibility_results
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_appointments_modtime ON appointments;
CREATE TRIGGER update_appointments_modtime
    BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_clinician_availability_modtime ON clinician_availability;
CREATE TRIGGER update_clinician_availability_modtime
    BEFORE UPDATE ON clinician_availability
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
