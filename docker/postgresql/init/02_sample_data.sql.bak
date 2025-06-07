-- Create sample accounts for development
-- This script is only for development/testing purposes

INSERT INTO accounts (id, name, status, created_at, updated_at)
VALUES 
    (uuid_generate_v4(), 'Test Hospital', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (uuid_generate_v4(), 'Medical Center', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Log the sample data creation
DO $$
BEGIN
    RAISE NOTICE 'Sample development data created for PostgreSQL';
END $$;
