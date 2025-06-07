"""Convert MySQL schema to PostgreSQL

Revision ID: postgresql_conversion
Revises: [latest_revision]
Create Date: 2025-06-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql

# revision identifiers, used by Alembic
revision = 'postgresql_conversion'
down_revision = None  # Update with latest revision
branch_labels = None
depends_on = None


def upgrade():
    """Convert schema from MySQL to PostgreSQL."""
    
    # Enable PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "hstore"')
    
    # Create enum types
    op.execute("""
        CREATE TYPE user_role AS ENUM ('patient', 'clinician', 'admin', 'super_admin', 'lab_tech');
        CREATE TYPE user_status AS ENUM ('active', 'inactive', 'invited', 'suspended');
        CREATE TYPE account_status AS ENUM ('active', 'inactive', 'suspended');
        CREATE TYPE patient_status AS ENUM ('active', 'inactive', 'archived');
        CREATE TYPE invite_status AS ENUM ('pending', 'completed', 'expired');
        CREATE TYPE chat_session_status AS ENUM ('in_progress', 'completed', 'abandoned');
        CREATE TYPE appointment_type AS ENUM ('virtual', 'in_person');
        CREATE TYPE appointment_status AS ENUM ('scheduled', 'completed', 'cancelled', 'no_show');
        CREATE TYPE lab_order_status AS ENUM ('ordered', 'processing', 'completed', 'cancelled');
        CREATE TYPE lab_result_status AS ENUM ('pending', 'available', 'reviewed');
    """)
    
    # Create updated_at trigger function
    op.execute('''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    ''')
    
    # Convert UUID columns from VARCHAR(36) to native UUID
    # Note: This assumes data has already been migrated
    uuid_columns = [
        ('accounts', 'id'),
        ('users', 'id'),
        ('users', 'account_id'),
        ('users', 'clinician_id'),
        ('patients', 'id'),
        ('patients', 'account_id'),
        ('patients', 'clinician_id'),
        ('patients', 'user_id'),
        ('chat_sessions', 'id'),
        ('chat_sessions', 'patient_id'),
        ('chat_sessions', 'clinician_id'),
        ('chat_answers', 'id'),
        ('chat_answers', 'session_id'),
        ('invites', 'id'),
        ('invites', 'patient_id'),
        ('invites', 'provider_id'),
        ('eligibility_results', 'id'),
        ('eligibility_results', 'patient_id'),
        ('eligibility_results', 'session_id'),
        ('eligibility_results', 'provider_id'),
        ('lab_orders', 'id'),
        ('lab_orders', 'patient_id'),
        ('lab_orders', 'provider_id'),
        ('lab_orders', 'eligibility_result_id'),
        ('lab_results', 'id'),
        ('lab_results', 'order_id'),
        ('lab_results', 'reviewer_id'),
        ('appointments', 'id'),
        ('appointments', 'patient_id'),
        ('appointments', 'clinician_id'),
        ('recurring_availability', 'id'),
        ('recurring_availability', 'clinician_id'),
    ]
    
    # Convert VARCHAR UUID columns to native UUID type
    for table, column in uuid_columns:
        try:
            op.execute(f'ALTER TABLE {table} ALTER COLUMN {column} TYPE UUID USING {column}::UUID')
        except Exception as e:
            print(f"Warning: Could not convert {table}.{column} to UUID: {e}")
    
    # Convert JSON columns to JSONB for better performance
    jsonb_columns = [
        ('chat_questions', 'options'),
        ('chat_questions', 'next_question_logic'),
        ('eligibility_results', 'factors'),
        ('lab_orders', 'insurance_information'),
        ('lab_results', 'result_data'),
        ('recurring_availability', 'days_of_week'),
        ('recurring_availability', 'time_slots'),
    ]
    
    for table, column in jsonb_columns:
        try:
            op.alter_column(table, column, type_=postgresql.JSONB())
        except Exception as e:
            print(f"Warning: Could not convert {table}.{column} to JSONB: {e}")
    
    # Apply updated_at triggers to tables
    tables_with_updated_at = [
        'accounts', 'users', 'patients', 'chat_sessions', 'chat_questions',
        'chat_answers', 'invites', 'eligibility_results', 'lab_orders',
        'lab_results', 'appointments', 'recurring_availability'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f'''
            CREATE TRIGGER update_{table}_updated_at 
                BEFORE UPDATE ON {table} 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column();
        ''')


def downgrade():
    """Downgrade is not supported for PostgreSQL conversion."""
    raise NotImplementedError("Downgrade from PostgreSQL to MySQL is not supported. Use database backup for rollback.")
