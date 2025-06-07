#!/usr/bin/env python3
"""
MySQL to PostgreSQL Migration Script for Genascope

This script performs the database migration from MySQL to PostgreSQL,
including schema conversion and data migration.

Usage:
    python migrate_to_postgresql.py --config config.yml
"""

import argparse
import logging
import sys
import yaml
import pymysql
import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MigrationConfig:
    """Configuration for the migration process."""
    
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
    
    @property
    def mysql_config(self) -> Dict[str, Any]:
        return self.config['mysql']
    
    @property
    def postgresql_config(self) -> Dict[str, Any]:
        return self.config['postgresql']
    
    @property
    def migration_options(self) -> Dict[str, Any]:
        return self.config.get('options', {})

class DatabaseMigrator:
    """Handles the migration from MySQL to PostgreSQL."""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.mysql_conn = None
        self.pg_conn = None
        
    def connect_databases(self):
        """Establish connections to both databases."""
        try:
            # Connect to MySQL
            self.mysql_conn = pymysql.connect(
                host=self.config.mysql_config['host'],
                port=self.config.mysql_config['port'],
                user=self.config.mysql_config['user'],
                password=self.config.mysql_config['password'],
                database=self.config.mysql_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info("Connected to MySQL database")
            
            # Connect to PostgreSQL
            self.pg_conn = psycopg2.connect(
                host=self.config.postgresql_config['host'],
                port=self.config.postgresql_config['port'],
                user=self.config.postgresql_config['user'],
                password=self.config.postgresql_config['password'],
                database=self.config.postgresql_config['database']
            )
            self.pg_conn.autocommit = False
            logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
    
    def setup_postgresql_extensions(self):
        """Enable required PostgreSQL extensions."""
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "hstore"')
                self.pg_conn.commit()
                logger.info("PostgreSQL extensions enabled")
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL extensions: {e}")
            raise
    
    def create_updated_at_trigger(self):
        """Create the updated_at trigger function and apply to tables."""
        trigger_function = '''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        '''
        
        tables_with_updated_at = [
            'accounts', 'users', 'patients', 'chat_sessions', 'chat_questions',
            'chat_answers', 'invites', 'eligibility_results', 'lab_orders',
            'lab_results', 'appointments', 'recurring_availability'
        ]
        
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute(trigger_function)
                
                for table in tables_with_updated_at:
                    trigger_sql = f'''
                    DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                    CREATE TRIGGER update_{table}_updated_at 
                        BEFORE UPDATE ON {table} 
                        FOR EACH ROW 
                        EXECUTE FUNCTION update_updated_at_column();
                    '''
                    cursor.execute(trigger_sql)
                
                self.pg_conn.commit()
                logger.info("Updated_at triggers created")
        except Exception as e:
            logger.error(f"Failed to create triggers: {e}")
            raise
    
    def convert_uuid(self, value: Optional[str]) -> Optional[str]:
        """Convert MySQL UUID string to PostgreSQL UUID format."""
        if value is None:
            return None
        try:
            # Validate and normalize UUID
            uuid_obj = uuid.UUID(value)
            return str(uuid_obj)
        except ValueError:
            logger.warning(f"Invalid UUID format: {value}")
            return str(uuid.uuid4())  # Generate new UUID if invalid
    
    def convert_json(self, value: Optional[str]) -> Optional[Dict]:
        """Convert MySQL JSON string to PostgreSQL JSONB."""
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        try:
            return json.loads(value) if value else None
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON format: {value}")
            return None
    
    def convert_boolean(self, value: Any) -> Optional[bool]:
        """Convert MySQL boolean representation to PostgreSQL boolean."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def migrate_table(self, table_name: str, transformations: Dict[str, callable] = None):
        """Migrate a single table from MySQL to PostgreSQL."""
        logger.info(f"Migrating table: {table_name}")
        
        try:
            # Get MySQL data
            with self.mysql_conn.cursor() as mysql_cursor:
                mysql_cursor.execute(f"SELECT * FROM {table_name}")
                rows = mysql_cursor.fetchall()
                
                if not rows:
                    logger.info(f"No data found in table {table_name}")
                    return
                
                logger.info(f"Found {len(rows)} rows in {table_name}")
                
                # Get column names
                columns = list(rows[0].keys())
                
                # Prepare PostgreSQL insert
                placeholders = ', '.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                with self.pg_conn.cursor() as pg_cursor:
                    for row in rows:
                        # Apply transformations
                        transformed_row = []
                        for col in columns:
                            value = row[col]
                            
                            # Apply specific transformations
                            if transformations and col in transformations:
                                value = transformations[col](value)
                            
                            transformed_row.append(value)
                        
                        pg_cursor.execute(insert_sql, transformed_row)
                    
                    self.pg_conn.commit()
                    logger.info(f"Successfully migrated {len(rows)} rows to {table_name}")
                    
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            self.pg_conn.rollback()
            raise
    
    def migrate_accounts(self):
        """Migrate accounts table."""
        transformations = {
            'id': self.convert_uuid,
        }
        self.migrate_table('accounts', transformations)
    
    def migrate_users(self):
        """Migrate users table."""
        transformations = {
            'id': self.convert_uuid,
            'account_id': self.convert_uuid,
            'clinician_id': self.convert_uuid,
            'is_active': self.convert_boolean,
        }
        self.migrate_table('users', transformations)
    
    def migrate_patients(self):
        """Migrate patients table."""
        transformations = {
            'id': self.convert_uuid,
            'account_id': self.convert_uuid,
            'clinician_id': self.convert_uuid,
            'user_id': self.convert_uuid,
        }
        self.migrate_table('patients', transformations)
    
    def migrate_chat_sessions(self):
        """Migrate chat_sessions table."""
        transformations = {
            'id': self.convert_uuid,
            'patient_id': self.convert_uuid,
            'clinician_id': self.convert_uuid,
        }
        self.migrate_table('chat_sessions', transformations)
    
    def migrate_chat_questions(self):
        """Migrate chat_questions table."""
        transformations = {
            'options': self.convert_json,
            'next_question_logic': self.convert_json,
            'is_active': self.convert_boolean,
        }
        self.migrate_table('chat_questions', transformations)
    
    def migrate_chat_answers(self):
        """Migrate chat_answers table."""
        transformations = {
            'id': self.convert_uuid,
            'session_id': self.convert_uuid,
        }
        self.migrate_table('chat_answers', transformations)
    
    def migrate_invites(self):
        """Migrate invites table."""
        transformations = {
            'id': self.convert_uuid,
            'patient_id': self.convert_uuid,
            'provider_id': self.convert_uuid,
        }
        self.migrate_table('invites', transformations)
    
    def migrate_eligibility_results(self):
        """Migrate eligibility_results table."""
        transformations = {
            'id': self.convert_uuid,
            'patient_id': self.convert_uuid,
            'session_id': self.convert_uuid,
            'provider_id': self.convert_uuid,
            'is_eligible': self.convert_boolean,
            'nccn_eligible': self.convert_boolean,
            'provider_reviewed': self.convert_boolean,
            'factors': self.convert_json,
        }
        self.migrate_table('eligibility_results', transformations)
    
    def migrate_lab_orders(self):
        """Migrate lab_orders table."""
        transformations = {
            'id': self.convert_uuid,
            'patient_id': self.convert_uuid,
            'provider_id': self.convert_uuid,
            'eligibility_result_id': self.convert_uuid,
            'insurance_information': self.convert_json,
        }
        self.migrate_table('lab_orders', transformations)
    
    def migrate_lab_results(self):
        """Migrate lab_results table."""
        transformations = {
            'id': self.convert_uuid,
            'order_id': self.convert_uuid,
            'reviewer_id': self.convert_uuid,
            'result_data': self.convert_json,
        }
        self.migrate_table('lab_results', transformations)
    
    def migrate_appointments(self):
        """Migrate appointments table."""
        transformations = {
            'id': self.convert_uuid,
            'patient_id': self.convert_uuid,
            'clinician_id': self.convert_uuid,
        }
        self.migrate_table('appointments', transformations)
    
    def migrate_recurring_availability(self):
        """Migrate recurring_availability table."""
        transformations = {
            'id': self.convert_uuid,
            'clinician_id': self.convert_uuid,
            'days_of_week': self.convert_json,
            'time_slots': self.convert_json,
        }
        self.migrate_table('recurring_availability', transformations)
    
    def validate_migration(self):
        """Validate the migration by comparing record counts and data integrity."""
        logger.info("Starting migration validation...")
        
        tables_to_validate = [
            'accounts', 'users', 'patients', 'chat_sessions', 'chat_questions',
            'chat_answers', 'invites', 'eligibility_results', 'lab_orders',
            'lab_results', 'appointments', 'recurring_availability'
        ]
        
        validation_results = {}
        
        for table in tables_to_validate:
            try:
                # Count MySQL records
                with self.mysql_conn.cursor() as mysql_cursor:
                    mysql_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    mysql_count = mysql_cursor.fetchone()['count']
                
                # Count PostgreSQL records
                with self.pg_conn.cursor() as pg_cursor:
                    pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    pg_count = pg_cursor.fetchone()[0]
                
                validation_results[table] = {
                    'mysql_count': mysql_count,
                    'postgresql_count': pg_count,
                    'match': mysql_count == pg_count
                }
                
                if mysql_count == pg_count:
                    logger.info(f"✓ {table}: {mysql_count} records migrated successfully")
                else:
                    logger.error(f"✗ {table}: MySQL({mysql_count}) != PostgreSQL({pg_count})")
                    
            except Exception as e:
                logger.error(f"Failed to validate table {table}: {e}")
                validation_results[table] = {'error': str(e)}
        
        # Summary
        successful_tables = sum(1 for result in validation_results.values() 
                              if result.get('match', False))
        total_tables = len(tables_to_validate)
        
        logger.info(f"Validation complete: {successful_tables}/{total_tables} tables migrated successfully")
        
        return validation_results
    
    def run_migration(self):
        """Execute the complete migration process."""
        logger.info("Starting MySQL to PostgreSQL migration...")
        
        try:
            # Connect to databases
            self.connect_databases()
            
            # Setup PostgreSQL
            self.setup_postgresql_extensions()
            self.create_updated_at_trigger()
            
            # Migrate tables in dependency order
            migration_order = [
                ('accounts', self.migrate_accounts),
                ('users', self.migrate_users),
                ('patients', self.migrate_patients),
                ('chat_questions', self.migrate_chat_questions),
                ('chat_sessions', self.migrate_chat_sessions),
                ('chat_answers', self.migrate_chat_answers),
                ('invites', self.migrate_invites),
                ('eligibility_results', self.migrate_eligibility_results),
                ('lab_orders', self.migrate_lab_orders),
                ('lab_results', self.migrate_lab_results),
                ('appointments', self.migrate_appointments),
                ('recurring_availability', self.migrate_recurring_availability),
            ]
            
            for table_name, migration_func in migration_order:
                try:
                    migration_func()
                except Exception as e:
                    logger.error(f"Failed to migrate {table_name}: {e}")
                    if not self.config.migration_options.get('continue_on_error', False):
                        raise
            
            # Validate migration
            validation_results = self.validate_migration()
            
            logger.info("Migration completed successfully!")
            return validation_results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            # Close connections
            if self.mysql_conn:
                self.mysql_conn.close()
            if self.pg_conn:
                self.pg_conn.close()

def create_sample_config():
    """Create a sample configuration file."""
    config = {
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'user': 'genascope',
            'password': 'genascope',
            'database': 'genascope'
        },
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'user': 'genascope',
            'password': 'genascope',
            'database': 'genascope'
        },
        'options': {
            'continue_on_error': False,
            'backup_before_migration': True,
            'validate_after_migration': True
        }
    }
    
    with open('migration_config.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("Sample configuration file created: migration_config.yml")
    print("Please update the configuration with your actual database credentials.")

def main():
    parser = argparse.ArgumentParser(description='Migrate Genascope from MySQL to PostgreSQL')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--create-config', action='store_true', 
                       help='Create a sample configuration file')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_sample_config()
        return
    
    try:
        config = MigrationConfig(args.config)
        migrator = DatabaseMigrator(config)
        validation_results = migrator.run_migration()
        
        # Print validation summary
        print("\n" + "="*50)
        print("MIGRATION VALIDATION SUMMARY")
        print("="*50)
        
        for table, result in validation_results.items():
            if 'error' in result:
                print(f"❌ {table}: ERROR - {result['error']}")
            elif result['match']:
                print(f"✅ {table}: {result['mysql_count']} records migrated successfully")
            else:
                print(f"❌ {table}: MISMATCH - MySQL({result['mysql_count']}) != PostgreSQL({result['postgresql_count']})")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
