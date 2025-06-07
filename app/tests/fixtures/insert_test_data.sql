-- Insert basic test data for PostgreSQL database
-- This creates minimal data to get the application running

-- Insert test accounts
INSERT INTO accounts (id, name, status, created_at, updated_at) VALUES 
    (uuid_generate_v4(), 'Test Hospital', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (uuid_generate_v4(), 'Medical Center', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Get the first account ID for foreign key references
WITH first_account AS (
    SELECT id FROM accounts LIMIT 1
)
-- Insert test users
INSERT INTO users (id, name, email, role, status, password_hash, account_id, created_at, updated_at) 
SELECT 
    uuid_generate_v4(),
    'Super Admin',
    'superadmin@genascope.com',
    'super_admin',
    'active',
    '$2b$12$TJANOGQCeto3ICLpfTWQy.KpqccLVyyvcIQfWqzC2oTkzDn6ipwgq', -- password: admin123
    NULL,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM first_account
ON CONFLICT (email) DO NOTHING;

WITH first_account AS (
    SELECT id FROM accounts LIMIT 1
)
INSERT INTO users (id, name, email, role, status, password_hash, account_id, created_at, updated_at)
SELECT 
    uuid_generate_v4(),
    'Test Admin',
    'admin@test.com',
    'admin',
    'active',
    '$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G', -- password: admin123
    first_account.id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM first_account
ON CONFLICT (email) DO NOTHING;

WITH first_account AS (
    SELECT id FROM accounts LIMIT 1
)
INSERT INTO users (id, name, email, role, status, password_hash, account_id, created_at, updated_at)
SELECT 
    uuid_generate_v4(),
    'Dr. Test Clinician',
    'clinician@test.com',
    'clinician',
    'active',
    '$2b$12$QjUyhpIh0PKVALn8Rf6j7e5p0Nu1bVxIuyKP9qFCmsP10HMmEQeA.', -- password: admin123
    first_account.id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM first_account
ON CONFLICT (email) DO NOTHING;

WITH first_account AS (
    SELECT id FROM accounts LIMIT 1
)
INSERT INTO users (id, name, email, role, status, password_hash, account_id, created_at, updated_at)
SELECT 
    uuid_generate_v4(),
    'Test Lab Tech',
    'labtech@test.com',
    'lab_tech',
    'active',
    '$2b$12$06lqTupwQjKza6agnXKp2OdBImIQB8/J1kCjDGx0VGRqkXbS58tXi', -- password: admin123
    first_account.id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM first_account
ON CONFLICT (email) DO NOTHING;

-- Create patient users first
WITH first_account AS (
    SELECT id FROM accounts LIMIT 1
)
INSERT INTO users (id, name, email, role, status, password_hash, account_id, created_at, updated_at)
SELECT 
    uuid_generate_v4(),
    'John Doe',
    'patient1@test.com',
    'patient',
    'active',
    '$2b$12$/7Vvu58rtfqFnd5/f9YgMeBwwQ.DbXFguDFVlK0NrZ.1KA9kQnEPq', -- password: admin123
    first_account.id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM first_account
ON CONFLICT (email) DO NOTHING;

WITH first_account AS (
    SELECT id FROM accounts LIMIT 1
)
INSERT INTO users (id, name, email, role, status, password_hash, account_id, created_at, updated_at)
SELECT 
    uuid_generate_v4(),
    'Jane Smith',
    'patient2@test.com',
    'patient',
    'active',
    '$2b$12$/7Vvu58rtfqFnd5/f9YgMeBwwQ.DbXFguDFVlK0NrZ.1KA9kQnEPq', -- password: admin123
    first_account.id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM first_account
ON CONFLICT (email) DO NOTHING;

-- Insert test patients (referencing the patient users)
WITH clinician_user AS (
    SELECT id FROM users WHERE email = 'clinician@test.com' LIMIT 1
),
patient_user AS (
    SELECT id FROM users WHERE email = 'patient1@test.com' LIMIT 1
),
first_account AS (
    SELECT id FROM accounts LIMIT 1
)
INSERT INTO patients (id, user_id, first_name, last_name, phone, status, created_at, updated_at, clinician_id, account_id)
SELECT 
    uuid_generate_v4(),
    patient_user.id,
    'John',
    'Doe',
    '+1-555-0101',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    clinician_user.id,
    first_account.id
FROM clinician_user, patient_user, first_account
ON CONFLICT DO NOTHING;

WITH clinician_user AS (
    SELECT id FROM users WHERE email = 'clinician@test.com' LIMIT 1
),
patient_user AS (
    SELECT id FROM users WHERE email = 'patient2@test.com' LIMIT 1
),
first_account AS (
    SELECT id FROM accounts LIMIT 1
)
INSERT INTO patients (id, user_id, first_name, last_name, phone, status, created_at, updated_at, clinician_id, account_id)
SELECT 
    uuid_generate_v4(),
    patient_user.id,
    'Jane',
    'Smith',
    '+1-555-0102',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    clinician_user.id,
    first_account.id
FROM clinician_user, patient_user, first_account
ON CONFLICT DO NOTHING;

-- Display summary of inserted data
SELECT 'accounts' as table_name, COUNT(*) as count FROM accounts
UNION ALL
SELECT 'users' as table_name, COUNT(*) as count FROM users  
UNION ALL
SELECT 'patients' as table_name, COUNT(*) as count FROM patients;

-- Display test users for reference
SELECT name, email, role, status FROM users ORDER BY role, name;
