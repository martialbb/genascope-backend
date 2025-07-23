#!/usr/bin/env python3
"""
This script adds the external_id column to the patients table.
"""
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

def add_external_id_column():
    """
    Add external_id column to the patients table.
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
        
        # Check if the external_id column already exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='patients' AND column_name='external_id'")
        if cur.fetchone() is None:
            print("Adding external_id column to patients table...")
            cur.execute("""
                ALTER TABLE patients 
                ADD COLUMN external_id VARCHAR(255) NULL;
                
                -- Create an index for better performance
                CREATE INDEX idx_patients_external_id ON patients(external_id);
            """)
            print("✅ external_id column added")
        else:
            print("✅ external_id column already exists")
        
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    if add_external_id_column():
        print("Successfully added external_id column to patients table!")
        sys.exit(0)
    else:
        print("Failed to add external_id column to patients table.")
        sys.exit(1)
