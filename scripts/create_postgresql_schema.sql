-- PostgreSQL-compatible schema creation
-- This replaces the problematic Alembic migrations for fresh PostgreSQL setup

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "hstore";

-- Create enum types
CREATE TYPE user_role AS ENUM ('patient', 'clinician', 'admin', 'super_admin', 'lab_tech');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'invited', 'suspended');
CREATE TYPE account_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE patient_status AS ENUM ('active', 'inactive', 'archived');
CREATE TYPE invite_status AS ENUM ('pending', 'completed', 'expired');
CREATE TYPE chat_session_status AS ENUM ('in_progress', 'completed', 'abandoned');
CREATE TYPE appointment_type AS ENUM ('virtual', 'in_person');
CREATE TYPE appointment_status AS ENUM ('scheduled', 'completed', 'cancelled', 'no_show');
CREATE TYPE lab_order_status AS ENUM ('ordered', 'processing', 'completed', 'cancelled');
CREATE TYPE lab_result_status AS ENUM ('pending', 'available', 'reviewed');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create tables (PostgreSQL-compatible)

-- Accounts table
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    status account_status DEFAULT 'active' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for accounts
CREATE TRIGGER update_accounts_updated_at 
    BEFORE UPDATE ON accounts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    role user_role NOT NULL,
    status user_status DEFAULT 'active' NOT NULL,
    clinician_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for users
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Patients table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id),
    user_id UUID REFERENCES users(id),
    clinician_id UUID REFERENCES users(id),
    status patient_status DEFAULT 'active' NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    date_of_birth DATE,
    phone VARCHAR(20),
    address TEXT,
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for patients
CREATE TRIGGER update_patients_updated_at 
    BEFORE UPDATE ON patients 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    clinician_id UUID REFERENCES users(id),
    status chat_session_status DEFAULT 'in_progress' NOT NULL,
    session_type VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for chat_sessions
CREATE TRIGGER update_chat_sessions_updated_at 
    BEFORE UPDATE ON chat_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Chat questions table
CREATE TABLE chat_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    options JSONB,
    next_question_logic JSONB,
    order_index INTEGER,
    is_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for chat_questions
CREATE TRIGGER update_chat_questions_updated_at 
    BEFORE UPDATE ON chat_questions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Chat answers table
CREATE TABLE chat_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id),
    question_id UUID REFERENCES chat_questions(id),
    answer_text TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for chat_answers
CREATE TRIGGER update_chat_answers_updated_at 
    BEFORE UPDATE ON chat_answers 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Invites table
CREATE TABLE invites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    provider_id UUID REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    status invite_status DEFAULT 'pending' NOT NULL,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for invites
CREATE TRIGGER update_invites_updated_at 
    BEFORE UPDATE ON invites 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Eligibility results table
CREATE TABLE eligibility_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    session_id UUID REFERENCES chat_sessions(id),
    provider_id UUID REFERENCES users(id),
    is_eligible BOOLEAN,
    confidence_score DECIMAL(3,2),
    factors JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for eligibility_results
CREATE TRIGGER update_eligibility_results_updated_at 
    BEFORE UPDATE ON eligibility_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Lab orders table
CREATE TABLE lab_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    provider_id UUID REFERENCES users(id),
    eligibility_result_id UUID REFERENCES eligibility_results(id),
    lab_api_order_id VARCHAR(255),
    status lab_order_status DEFAULT 'ordered' NOT NULL,
    ordered_tests TEXT[],
    insurance_information JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for lab_orders
CREATE TRIGGER update_lab_orders_updated_at 
    BEFORE UPDATE ON lab_orders 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Lab results table
CREATE TABLE lab_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES lab_orders(id),
    lab_api_result_id VARCHAR(255),
    status lab_result_status DEFAULT 'pending' NOT NULL,
    result_data JSONB,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for lab_results
CREATE TRIGGER update_lab_results_updated_at 
    BEFORE UPDATE ON lab_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Appointments table
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    clinician_id UUID REFERENCES users(id),
    appointment_type appointment_type NOT NULL,
    status appointment_status DEFAULT 'scheduled' NOT NULL,
    scheduled_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    date DATE,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for appointments
CREATE TRIGGER update_appointments_updated_at 
    BEFORE UPDATE ON appointments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Recurring availability table
CREATE TABLE recurring_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinician_id UUID REFERENCES users(id),
    days_of_week JSONB NOT NULL,
    time_slots JSONB NOT NULL,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for recurring_availability
CREATE TRIGGER update_recurring_availability_updated_at 
    BEFORE UPDATE ON recurring_availability 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Risk assessments table
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    session_id UUID REFERENCES chat_sessions(id),
    risk_score DECIMAL(3,2),
    risk_level VARCHAR(20),
    factors JSONB,
    recommendations TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create trigger for risk_assessments
CREATE TRIGGER update_risk_assessments_updated_at 
    BEFORE UPDATE ON risk_assessments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_account_id ON users(account_id);
CREATE INDEX idx_patients_user_id ON patients(user_id);
CREATE INDEX idx_patients_clinician_id ON patients(clinician_id);
CREATE INDEX idx_chat_sessions_patient_id ON chat_sessions(patient_id);
CREATE INDEX idx_chat_answers_session_id ON chat_answers(session_id);
CREATE INDEX idx_invites_token ON invites(token);
CREATE INDEX idx_invites_email ON invites(email);
CREATE INDEX idx_lab_orders_patient_id ON lab_orders(patient_id);
CREATE INDEX idx_lab_results_order_id ON lab_results(order_id);
CREATE INDEX idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX idx_appointments_clinician_id ON appointments(clinician_id);
