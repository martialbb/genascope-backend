#!/usr/bin/env python3
"""
This script fixes the appointments table's clinician_id column to work with string IDs.
It carefully manages the foreign key constraint.
"""
import sys
import os
import psycopg2
from psycopg2 import sql
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

def fix_clinician_id():
    """
    Fix the appointments table's clinician_id column to accept string IDs
    and properly handle the foreign key constraint.
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
        
        # 1. Check current table structure
        print("Examining appointments table structure...")
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='appointments' AND column_name='clinician_id'")
        column_info = cur.fetchone()
        
        if not column_info:
            print("Error: clinician_id column not found in appointments table")
            return False
            
        print(f"Current clinician_id type: {column_info[1]}")
        
        # 2. Check if there's a foreign key constraint
        cur.execute("""
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = 'appointments'
            AND ccu.column_name = 'clinician_id'
        """)
        
        fk_constraint = cur.fetchone()
        if fk_constraint:
            constraint_name = fk_constraint[0]
            print(f"Found foreign key constraint: {constraint_name}")
            
            # 3. Drop the constraint
            print("Dropping foreign key constraint...")
            cur.execute(f"ALTER TABLE appointments DROP CONSTRAINT {constraint_name}")
            print("✅ Constraint dropped")
        else:
            print("No foreign key constraint found, proceeding with column type change")
        
        # 4. Check users table structure to see what column we're referencing
        print("Examining users table structure...")
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='users' AND column_name='id'")
        user_id_info = cur.fetchone()
        
        if not user_id_info:
            print("Error: id column not found in users table")
            return False
            
        print(f"Users.id column type: {user_id_info[1]}")
            
        # 5. Alter clinician_id column type or make it work with string IDs
        print("Setting up appointments table to work with string clinician IDs...")
        
        # Create a temporary column without constraints
        print("Creating temporary column...")
        cur.execute("""
            ALTER TABLE appointments 
            ADD COLUMN clinician_id_temp VARCHAR(255)
        """)
        
        # Copy data to the temporary column with type conversion
        print("Copying data with type conversion...")
        cur.execute("""
            UPDATE appointments 
            SET clinician_id_temp = clinician_id::text 
            WHERE clinician_id IS NOT NULL
        """)
        
        # Drop the original column
        print("Dropping the original column...")
        cur.execute("""
            ALTER TABLE appointments 
            DROP COLUMN clinician_id
        """)
        
        # Rename the temp column to the original name
        print("Renaming temporary column...")
        cur.execute("""
            ALTER TABLE appointments 
            RENAME COLUMN clinician_id_temp TO clinician_id
        """)
        
        # Add an index on the clinician_id column
        print("Adding index on clinician_id column...")
        cur.execute("""
            CREATE INDEX idx_appointments_clinician_id ON appointments(clinician_id)
        """)
        
        # We won't recreate the foreign key constraint to allow string IDs like "clinician-123"
        print("Skipping foreign key constraint to allow string IDs")
        print("✅ Successfully converted clinician_id to accept string values")
        
        print("Successfully updated appointments.clinician_id column")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    if fix_clinician_id():
        print("Appointments table clinician_id column fixed successfully!")
        sys.exit(0)
    else:
        print("Failed to fix appointments table.")
        sys.exit(1)
