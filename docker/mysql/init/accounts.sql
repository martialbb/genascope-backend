geneh -- accounts.sql - Create accounts table and add sample data
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL
);

-- Check if there are any accounts before adding sample data
INSERT INTO accounts (id, name, domain, is_active, created_at)
SELECT 'acc-001', 'Test Hospital', 'testhospital.org', 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM accounts);

INSERT INTO accounts (id, name, domain, is_active, created_at)
SELECT 'acc-002', 'Medical Center', 'medcenter.org', 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM accounts);
