#!/bin/bash

echo "🚀 Starting GenAScope Backend..."
echo "🌟 GenAScope Backend Deployment"

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
echo "📡 Checking database connectivity to $DATABASE_HOST..."
nc -z $DATABASE_HOST 5432
while [ $? -ne 0 ]; do
    echo "🔄 Database not ready, waiting..."
    sleep 2
    nc -z $DATABASE_HOST 5432
done
echo "✅ Database is ready!"

# Simple database setup - only create essential tables for authentication
echo "🔄 Setting up essential database schema..."
export PYTHONPATH=/app

python -c "
import os
import psycopg2

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    cur = conn.cursor()
    
    print('✅ Connected to database successfully')
    
    # Drop existing tables if they exist
    print('🧹 Cleaning existing tables...')
    cur.execute('DROP TABLE IF EXISTS users CASCADE')
    cur.execute('DROP TABLE IF EXISTS accounts CASCADE')
    cur.execute('DROP TABLE IF EXISTS alembic_version CASCADE')
    print('✅ Cleaned existing tables')
    
    # Create essential tables for authentication
    print('🏗️ Creating essential tables...')
    
    # Create accounts table
    cur.execute('''
        CREATE TABLE accounts (
            id VARCHAR PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            domain VARCHAR(255),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print('✅ Created accounts table')
    
    # Create users table  
    cur.execute('''
        CREATE TABLE users (
            id VARCHAR PRIMARY KEY,
            account_id VARCHAR REFERENCES accounts(id) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print('✅ Created users table')
    
    # Create basic indexes
    cur.execute('CREATE INDEX ix_users_email ON users (email)')
    print('✅ Created indexes')
    
    # Initialize alembic version table
    cur.execute('''
        CREATE TABLE alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
    ''')
    cur.execute(\"INSERT INTO alembic_version (version_num) VALUES ('simple_setup')\")
    print('✅ Initialized alembic version table')
    
    # Create default account and admin user
    import bcrypt
    password_hash = bcrypt.hashpw('test123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cur.execute(\"\"\"
        INSERT INTO accounts (id, name, domain, is_active) 
        VALUES ('default-account', 'Default Account', 'default.com', true)
    \"\"\")
    
    cur.execute(\"\"\"
        INSERT INTO users (id, account_id, email, hashed_password, full_name, is_active, is_superuser) 
        VALUES ('admin-user', 'default-account', 'admin@test.com', %s, 'Admin User', true, true)
    \"\"\", (password_hash,))
    
    print('✅ Created default account and admin user')
    print('🎯 Admin credentials: admin@test.com / test123')
    
    cur.close()
    conn.close()
    print('🎉 Database setup completed successfully!')
    
except Exception as e:
    print(f'❌ Database setup failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

echo "🚀 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
