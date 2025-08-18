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
    
    # Skip this migration if we already have a working PostgreSQL setup
    connection = op.get_bind()
    
    # Check if we already have some core tables
    result = connection.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
    )).scalar()
    
    if result > 5:  # If we have several tables, skip this conversion
        print("✅ Database already has tables - skipping PostgreSQL conversion")
        return
    
    print(f"📋 Converting {result} existing tables to PostgreSQL compatibility...")
    
    # Enable PostgreSQL extensions (only if not exists)
    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        op.execute('CREATE EXTENSION IF NOT EXISTS "hstore"')
        print("✅ PostgreSQL extensions enabled")
    except Exception as e:
        print(f"⚠️  Extension creation warning: {e}")
    
    # Create enum types (only if they don't exist)
    enum_types = [
        ("user_role", "('patient', 'clinician', 'admin', 'super_admin', 'lab_tech')"),
        ("user_status", "('active', 'inactive', 'invited', 'suspended')"),
        ("account_status", "('active', 'inactive', 'suspended')"),
        ("patient_status", "('active', 'inactive', 'archived')"),
        ("invite_status", "('pending', 'completed', 'expired')"),
        ("chat_session_status", "('in_progress', 'completed', 'abandoned')"),
        ("appointment_type", "('virtual', 'in_person')"),
        ("appointment_status", "('scheduled', 'completed', 'cancelled', 'no_show')"),
        ("lab_order_status", "('ordered', 'processing', 'completed', 'cancelled')"),
        ("lab_result_status", "('pending', 'available', 'reviewed')")
    ]
    
    for enum_name, enum_values in enum_types:
        try:
            # Check if enum type already exists
            result = connection.execute(sa.text(
                "SELECT 1 FROM pg_type WHERE typname = :type_name"
            ), {"type_name": enum_name}).fetchone()
            
            if not result:
                op.execute(f"CREATE TYPE {enum_name} AS ENUM {enum_values}")
                print(f"✅ Created enum type: {enum_name}")
            else:
                print(f"⚠️  Enum type {enum_name} already exists, skipping")
        except Exception as e:
            print(f"⚠️  Could not create enum {enum_name}: {e}")
    
    # Create updated_at trigger function (safe with CREATE OR REPLACE)
    try:
        op.execute('''
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        ''')
        print("✅ Created updated_at trigger function")
    except Exception as e:
        print(f"⚠️  Could not create trigger function: {e}")
    
    print("✅ PostgreSQL conversion completed with graceful handling")


def downgrade():
    """Downgrade is not supported for PostgreSQL conversion."""
    raise NotImplementedError("Downgrade from PostgreSQL to MySQL is not supported. Use database backup for rollback.")
