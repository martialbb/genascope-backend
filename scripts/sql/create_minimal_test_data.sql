-- Create minimal test data for the genascope database
-- This script creates basic data needed to test functionality

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insert test accounts
INSERT INTO accounts (id, name, created_at, updated_at) VALUES 
    (uuid_generate_v4(), 'Test Hospital', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Insert test users
DO $$
DECLARE
    account_uuid TEXT;
    user_uuid TEXT;
BEGIN
    -- Get first account ID
    SELECT id INTO account_uuid FROM accounts LIMIT 1;
    
    -- Insert users with correct column names
    INSERT INTO users (id, name, email, role, hashed_password, account_id, is_active, created_at, updated_at) VALUES 
        (uuid_generate_v4(), 'Super Admin', 'superadmin@genascope.com', 'super_admin', '$2b$12$TJANOGQCeto3ICLpfTWQy.KpqccLVyyvcIQfWqzC2oTkzDn6ipwgq', NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name;
    
    INSERT INTO users (id, name, email, role, hashed_password, account_id, is_active, created_at, updated_at) VALUES 
        (uuid_generate_v4(), 'Test Admin', 'admin@test.com', 'admin', '$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G', account_uuid, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name;
    
    INSERT INTO users (id, name, email, role, hashed_password, account_id, is_active, created_at, updated_at) VALUES 
        (uuid_generate_v4(), 'Test Clinician', 'clinician@test.com', 'clinician', '$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G', account_uuid, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name;
    
    INSERT INTO users (id, name, email, role, hashed_password, account_id, is_active, created_at, updated_at) VALUES 
        (uuid_generate_v4(), 'Test Patient User', 'patient@test.com', 'patient', '$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G', account_uuid, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name;
    
    -- Get the patient user ID and create patient record
    SELECT id INTO user_uuid FROM users WHERE email = 'patient@test.com';
    
    INSERT INTO patients (id, user_id, created_at, updated_at) VALUES 
        (uuid_generate_v4(), user_uuid, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT DO NOTHING;
    
    -- Insert basic chat strategy
    INSERT INTO chat_strategies (id, name, description, system_prompt, is_active, created_at, updated_at) VALUES 
        (uuid_generate_v4(), 'Test Cardiac Assessment', 'Basic test strategy for cardiac assessment', 'You are a helpful medical assistant conducting a cardiac risk assessment.', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT DO NOTHING;
    
    -- Insert basic knowledge source
    INSERT INTO knowledge_sources (id, name, description, processing_status, uploaded_by, created_at, updated_at) VALUES 
        (uuid_generate_v4(), 'Test Cardiac Guidelines', 'Basic cardiac risk guidelines for testing', 'completed', (SELECT id FROM users WHERE email = 'admin@test.com'), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT DO NOTHING;

END $$;

-- Display what was created
SELECT 'Data Summary' as section, 'Accounts' as type, COUNT(*)::text as count FROM accounts
UNION ALL
SELECT 'Data Summary', 'Users', COUNT(*)::text FROM users
UNION ALL  
SELECT 'Data Summary', 'Patients', COUNT(*)::text FROM patients
UNION ALL
SELECT 'Data Summary', 'Chat Strategies', COUNT(*)::text FROM chat_strategies
UNION ALL
SELECT 'Data Summary', 'Knowledge Sources', COUNT(*)::text FROM knowledge_sources;

-- Display login credentials
SELECT 'Login Info' as section, name as type, email as count FROM users WHERE email IN ('superadmin@genascope.com', 'admin@test.com', 'clinician@test.com', 'patient@test.com') ORDER BY role;
