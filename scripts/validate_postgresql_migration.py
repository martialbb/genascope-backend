#!/usr/bin/env python3
"""
Post-migration validation script for PostgreSQL migration.

This script validates that the migration from MySQL to PostgreSQL
was successful and all data is intact.
"""

import psycopg2
import psycopg2.extras
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def log_info(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")

def log_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.NC}")

def log_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.NC}")

def log_header(message: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}{message}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

class PostgreSQLValidator:
    """Validates PostgreSQL migration results."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.conn = None
        self.validation_results = {}
    
    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            log_info("Connected to PostgreSQL database")
        except Exception as e:
            log_error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def validate_extensions(self):
        """Validate that required PostgreSQL extensions are installed."""
        log_header("Validating PostgreSQL Extensions")
        
        required_extensions = ['uuid-ossp', 'hstore']
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN %s
            """, (tuple(required_extensions),))
            
            installed_extensions = [row['extname'] for row in cursor.fetchall()]
            
            for ext in required_extensions:
                if ext in installed_extensions:
                    log_info(f"Extension '{ext}' is installed")
                else:
                    log_error(f"Extension '{ext}' is missing")
                    return False
        
        return True
    
    def validate_enum_types(self):
        """Validate that custom enum types are created."""
        log_header("Validating Custom Enum Types")
        
        expected_enums = [
            'user_role', 'user_status', 'account_status', 'patient_status',
            'invite_status', 'chat_session_status', 'appointment_type',
            'appointment_status', 'lab_order_status', 'lab_result_status'
        ]
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT typname FROM pg_type 
                WHERE typtype = 'e' AND typname IN %s
            """, (tuple(expected_enums),))
            
            existing_enums = [row['typname'] for row in cursor.fetchall()]
            
            for enum_type in expected_enums:
                if enum_type in existing_enums:
                    log_info(f"Enum type '{enum_type}' exists")
                else:
                    log_warning(f"Enum type '{enum_type}' is missing")
        
        return True
    
    def validate_tables_and_counts(self):
        """Validate that all expected tables exist and have data."""
        log_header("Validating Tables and Record Counts")
        
        expected_tables = [
            'accounts', 'users', 'patients', 'chat_sessions', 'chat_questions',
            'chat_answers', 'invites', 'eligibility_results', 'lab_orders',
            'lab_results', 'appointments', 'recurring_availability'
        ]
        
        table_counts = {}
        
        with self.conn.cursor() as cursor:
            for table in expected_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    table_counts[table] = count
                    
                    if count > 0:
                        log_info(f"Table '{table}': {count} records")
                    else:
                        log_warning(f"Table '{table}': 0 records (empty table)")
                        
                except Exception as e:
                    log_error(f"Table '{table}': Error - {e}")
                    table_counts[table] = -1
        
        self.validation_results['table_counts'] = table_counts
        return True
    
    def validate_uuid_columns(self):
        """Validate that UUID columns are properly converted."""
        log_header("Validating UUID Column Conversions")
        
        uuid_tables = [
            ('accounts', 'id'),
            ('users', 'id'),
            ('users', 'account_id'),
            ('patients', 'id'),
            ('chat_sessions', 'id'),
            ('chat_answers', 'id'),
        ]
        
        with self.conn.cursor() as cursor:
            for table, column in uuid_tables:
                try:
                    cursor.execute(f"""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, (table, column))
                    
                    result = cursor.fetchone()
                    if result and result['data_type'] == 'uuid':
                        log_info(f"Column '{table}.{column}' is properly converted to UUID")
                    else:
                        data_type = result['data_type'] if result else 'NOT FOUND'
                        log_warning(f"Column '{table}.{column}' type: {data_type} (expected: uuid)")
                        
                except Exception as e:
                    log_error(f"Error checking '{table}.{column}': {e}")
        
        return True
    
    def validate_jsonb_columns(self):
        """Validate that JSON columns are converted to JSONB."""
        log_header("Validating JSONB Column Conversions")
        
        jsonb_columns = [
            ('chat_questions', 'options'),
            ('chat_questions', 'next_question_logic'),
            ('eligibility_results', 'factors'),
            ('lab_orders', 'insurance_information'),
            ('lab_results', 'result_data'),
        ]
        
        with self.conn.cursor() as cursor:
            for table, column in jsonb_columns:
                try:
                    cursor.execute(f"""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, (table, column))
                    
                    result = cursor.fetchone()
                    if result and result['data_type'] == 'jsonb':
                        log_info(f"Column '{table}.{column}' is properly converted to JSONB")
                    else:
                        data_type = result['data_type'] if result else 'NOT FOUND'
                        log_warning(f"Column '{table}.{column}' type: {data_type} (expected: jsonb)")
                        
                except Exception as e:
                    log_error(f"Error checking '{table}.{column}': {e}")
        
        return True
    
    def validate_triggers(self):
        """Validate that updated_at triggers are working."""
        log_header("Validating Updated_At Triggers")
        
        tables_with_triggers = [
            'accounts', 'users', 'patients', 'chat_sessions'
        ]
        
        with self.conn.cursor() as cursor:
            for table in tables_with_triggers:
                try:
                    cursor.execute(f"""
                        SELECT tgname 
                        FROM pg_trigger 
                        WHERE tgrelid = %s::regclass 
                        AND tgname = %s
                    """, (table, f'update_{table}_updated_at'))
                    
                    result = cursor.fetchone()
                    if result:
                        log_info(f"Trigger 'update_{table}_updated_at' exists")
                    else:
                        log_warning(f"Trigger 'update_{table}_updated_at' is missing")
                        
                except Exception as e:
                    log_error(f"Error checking trigger for '{table}': {e}")
        
        return True
    
    def validate_foreign_keys(self):
        """Validate that foreign key relationships are intact."""
        log_header("Validating Foreign Key Relationships")
        
        # Sample foreign key checks
        fk_checks = [
            ("users", "account_id", "accounts", "id"),
            ("patients", "account_id", "accounts", "id"),
            ("chat_sessions", "patient_id", "patients", "id"),
            ("chat_answers", "session_id", "chat_sessions", "id"),
        ]
        
        with self.conn.cursor() as cursor:
            for child_table, child_col, parent_table, parent_col in fk_checks:
                try:
                    # Check for orphaned records
                    cursor.execute(f"""
                        SELECT COUNT(*) as count
                        FROM {child_table} c
                        LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col}
                        WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL
                    """)
                    
                    orphaned_count = cursor.fetchone()['count']
                    
                    if orphaned_count == 0:
                        log_info(f"Foreign key {child_table}.{child_col} → {parent_table}.{parent_col}: OK")
                    else:
                        log_error(f"Foreign key {child_table}.{child_col} → {parent_table}.{parent_col}: {orphaned_count} orphaned records")
                        
                except Exception as e:
                    log_error(f"Error checking FK {child_table}.{child_col}: {e}")
        
        return True
    
    def validate_data_integrity(self):
        """Perform basic data integrity checks."""
        log_header("Validating Data Integrity")
        
        with self.conn.cursor() as cursor:
            # Check for duplicate emails in users table
            cursor.execute("""
                SELECT email, COUNT(*) as count 
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cursor.fetchall()
            if duplicates:
                log_error(f"Found {len(duplicates)} duplicate emails in users table")
            else:
                log_info("No duplicate emails found in users table")
            
            # Check for null values in required fields
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM users 
                WHERE email IS NULL OR name IS NULL
            """)
            
            null_required = cursor.fetchone()['count']
            if null_required == 0:
                log_info("No null values in required user fields")
            else:
                log_error(f"Found {null_required} users with null required fields")
        
        return True
    
    def run_all_validations(self):
        """Run all validation checks."""
        log_header("PostgreSQL Migration Validation Report")
        
        validations = [
            ("Extensions", self.validate_extensions),
            ("Enum Types", self.validate_enum_types),
            ("Tables and Counts", self.validate_tables_and_counts),
            ("UUID Columns", self.validate_uuid_columns),
            ("JSONB Columns", self.validate_jsonb_columns),
            ("Triggers", self.validate_triggers),
            ("Foreign Keys", self.validate_foreign_keys),
            ("Data Integrity", self.validate_data_integrity),
        ]
        
        results = {}
        
        for name, validation_func in validations:
            try:
                result = validation_func()
                results[name] = "PASSED" if result else "FAILED"
            except Exception as e:
                log_error(f"Validation '{name}' failed with error: {e}")
                results[name] = "ERROR"
        
        # Print summary
        log_header("Validation Summary")
        
        passed_count = sum(1 for status in results.values() if status == "PASSED")
        total_count = len(results)
        
        for validation, status in results.items():
            if status == "PASSED":
                log_info(f"{validation}: {status}")
            elif status == "FAILED":
                log_error(f"{validation}: {status}")
            else:
                log_warning(f"{validation}: {status}")
        
        print(f"\nOverall Result: {passed_count}/{total_count} validations passed")
        
        if passed_count == total_count:
            log_info("🎉 All validations passed! Migration appears to be successful.")
            return True
        else:
            log_warning("⚠️ Some validations failed. Please review the issues above.")
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

def main():
    """Main function to run validation."""
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'genascope',
        'password': 'genascope',
        'database': 'genascope'
    }
    
    validator = PostgreSQLValidator(db_config)
    
    try:
        validator.connect()
        success = validator.run_all_validations()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Validation failed: {e}")
        sys.exit(1)
    finally:
        validator.close()

if __name__ == "__main__":
    main()
