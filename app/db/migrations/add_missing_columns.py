import sys
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# Get database connection details from environment or use defaults
DATABASE_URI = os.environ.get("DATABASE_URI", "postgresql://genascope:genascope@localhost:5432/genascope")

# Parse the DATABASE_URI
parts = DATABASE_URI.split("//")[1].split("@")
user_pass = parts[0].split(":")
host_port_db = parts[1].split("/")
db_name = host_port_db[1]
host_port = host_port_db[0].split(":")

DB_USER = user_pass[0]
DB_PASSWORD = user_pass[1]
DB_HOST = host_port[0]
DB_PORT = int(host_port[1]) if len(host_port) > 1 else 5432

def run_migration():
    """
    Add missing columns to the database tables:
    1. invite_token to invites table
    2. time to appointments table
    3. notes to patients table
    4. clinician_id to invites table
    5. custom_message to invites table
    6. session_metadata to invites table
    7. expires_at to invites table
    8. accepted_at to invites table
    9. confirmation_code to appointments table
    10. email to patients table
    """
    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=db_name,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create extension if it doesn't exist (needed for UUID generation)
        cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        
        # Check and add invite_token column to invites table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='invites' AND column_name='invite_token'")
        if cur.fetchone() is None:
            print("Adding invite_token column to invites table...")
            cur.execute("""
                ALTER TABLE invites 
                ADD COLUMN invite_token VARCHAR(255) NOT NULL DEFAULT uuid_generate_v4();
                
                -- Create unique constraint
                ALTER TABLE invites 
                ADD CONSTRAINT unique_invite_token UNIQUE (invite_token);
            """)
            print("✅ invite_token column added")
        else:
            print("✅ invite_token column already exists")

        # Check and add time column to appointments table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='appointments' AND column_name='time'")
        if cur.fetchone() is None:
            print("Adding time column to appointments table...")
            cur.execute("""
                ALTER TABLE appointments 
                ADD COLUMN time VARCHAR(50) NULL;
            """)
            print("✅ time column added")
        else:
            print("✅ time column already exists")

        # Check and add notes column to patients table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='patients' AND column_name='notes'")
        if cur.fetchone() is None:
            print("Adding notes column to patients table...")
            cur.execute("""
                ALTER TABLE patients 
                ADD COLUMN notes TEXT NULL;
            """)
            print("✅ notes column added")
        else:
            print("✅ notes column already exists")

        # Check and add email column to patients table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='patients' AND column_name='email'")
        if cur.fetchone() is None:
            print("Adding email column to patients table...")
            cur.execute("""
                ALTER TABLE patients 
                ADD COLUMN email VARCHAR(255) NULL;
            """)
            print("✅ email column added")
        else:
            print("✅ email column already exists")

        # Check and add clinician_id column to invites table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='invites' AND column_name='clinician_id'")
        if cur.fetchone() is None:
            print("Adding clinician_id column to invites table...")
            cur.execute("""
                ALTER TABLE invites 
                ADD COLUMN clinician_id UUID NULL;
            """)
            print("✅ clinician_id column added")
        else:
            print("✅ clinician_id column already exists")

        # Check and add custom_message column to invites table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='invites' AND column_name='custom_message'")
        if cur.fetchone() is None:
            print("Adding custom_message column to invites table...")
            cur.execute("""
                ALTER TABLE invites 
                ADD COLUMN custom_message TEXT NULL;
            """)
            print("✅ custom_message column added")
        else:
            print("✅ custom_message column already exists")

        # Check and add session_metadata column to invites table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='invites' AND column_name='session_metadata'")
        if cur.fetchone() is None:
            print("Adding session_metadata column to invites table...")
            cur.execute("""
                ALTER TABLE invites 
                ADD COLUMN session_metadata JSONB NULL;
            """)
            print("✅ session_metadata column added")
        else:
            print("✅ session_metadata column already exists")

        # Check and add expires_at column to invites table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='invites' AND column_name='expires_at'")
        if cur.fetchone() is None:
            print("Adding expires_at column to invites table...")
            cur.execute("""
                ALTER TABLE invites 
                ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE NULL;
            """)
            print("✅ expires_at column added")
        else:
            print("✅ expires_at column already exists")

        # Check and add accepted_at column to invites table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='invites' AND column_name='accepted_at'")
        if cur.fetchone() is None:
            print("Adding accepted_at column to invites table...")
            cur.execute("""
                ALTER TABLE invites 
                ADD COLUMN accepted_at TIMESTAMP WITH TIME ZONE NULL;
            """)
            print("✅ accepted_at column added")
        else:
            print("✅ accepted_at column already exists")

        # Check and add confirmation_code column to appointments table
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='appointments' AND column_name='confirmation_code'")
        if cur.fetchone() is None:
            print("Adding confirmation_code column to appointments table...")
            cur.execute("""
                ALTER TABLE appointments 
                ADD COLUMN confirmation_code VARCHAR(50) NULL;
            """)
            print("✅ confirmation_code column added")
        else:
            print("✅ confirmation_code column already exists")

        # Update clinician_id column type in appointments table to accept string format
        print("Updating clinician_id column type in appointments table...")
        try:
            # First, try to alter the column type if it's UUID
            cur.execute("""
                ALTER TABLE appointments 
                ALTER COLUMN clinician_id TYPE VARCHAR(255) USING clinician_id::text;
            """)
            print("✅ Converted clinician_id column from UUID to VARCHAR")
        except Exception as e:
            print(f"Note: Could not convert clinician_id column type: {e}")

        print("All migrations completed successfully.")

    except Exception as e:
        print(f"Error executing migration: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run_migration()