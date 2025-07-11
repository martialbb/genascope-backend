-- Create basic test data for the genascope database
-- This script creates minimal data needed to test the AI chat functionality

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insert test accounts
INSERT INTO accounts (id, name, created_at, updated_at) VALUES 
    (uuid_generate_v4(), 'Test Hospital', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (uuid_generate_v4(), 'Medical Center', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Get the first account ID for foreign key references
DO $$
DECLARE
    account_uuid TEXT;
    user_uuid TEXT;
    patient_uuid TEXT;
    strategy_uuid TEXT;
    knowledge_uuid TEXT;
BEGIN
    -- Get first account ID
    SELECT id INTO account_uuid FROM accounts LIMIT 1;
    
    -- Insert test users with corrected column names
    INSERT INTO users (id, name, email, role, hashed_password, account_id, is_active, created_at, updated_at) VALUES 
        (uuid_generate_v4(), 'Super Admin', 'superadmin@genascope.com', 'super_admin', '$2b$12$TJANOGQCeto3ICLpfTWQy.KpqccLVyyvcIQfWqzC2oTkzDn6ipwgq', NULL, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (uuid_generate_v4(), 'Test Admin', 'admin@test.com', 'admin', '$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G', account_uuid, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (uuid_generate_v4(), 'Test Clinician', 'clinician@test.com', 'clinician', '$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G', account_uuid, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (uuid_generate_v4(), 'Test Patient User', 'patient@test.com', 'patient', '$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G', account_uuid, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (email) DO NOTHING;
    
    -- Get the patient user ID
    SELECT id INTO user_uuid FROM users WHERE email = 'patient@test.com';
    
    -- Insert test patient
    INSERT INTO patients (id, user_id, created_at, updated_at) VALUES 
        (uuid_generate_v4(), user_uuid, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT DO NOTHING;
    
    -- Get patient ID for chat strategy
    SELECT id INTO patient_uuid FROM patients LIMIT 1;
    
    -- Insert test chat strategy
    INSERT INTO chat_strategies (
        id, name, description, account_id, created_by, version, is_active, 
        created_at, updated_at
    ) VALUES (
        uuid_generate_v4(), 
        'Test Cardiac Assessment Strategy', 
        'A test strategy for cardiac risk assessment',
        account_uuid,
        (SELECT id FROM users WHERE email = 'admin@test.com'),
        1,
        true,
        CURRENT_TIMESTAMP, 
        CURRENT_TIMESTAMP
    ) ON CONFLICT DO NOTHING;
    
    -- Get strategy ID
    SELECT id INTO strategy_uuid FROM chat_strategies LIMIT 1;
    
    -- Insert test knowledge source
    INSERT INTO knowledge_sources (
        id, name, source_type, description, processing_status, is_active, 
        access_level, created_by, account_id, created_at, updated_at
    ) VALUES (
        uuid_generate_v4(),
        'Cardiac Risk Guidelines',
        'text',
        'Test knowledge source for cardiac risk assessment',
        'completed',
        true,
        'private',
        (SELECT id FROM users WHERE email = 'admin@test.com'),
        account_uuid,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ) ON CONFLICT DO NOTHING;

END $$;

-- Display what was created
SELECT 'Accounts created:' as info, COUNT(*) as count FROM accounts
UNION ALL
SELECT 'Users created:', COUNT(*) FROM users
UNION ALL  
SELECT 'Patients created:', COUNT(*) FROM patients
UNION ALL
SELECT 'Chat strategies created:', COUNT(*) FROM chat_strategies
UNION ALL
SELECT 'Knowledge sources created:', COUNT(*) FROM knowledge_sources;

-- Display user details for login
SELECT 'Login details:' as info, name, email, role FROM users ORDER BY role, name;
