"""Reset database with clean schema

Revision ID: 020_reset_database_clean
Revises: merge_heads_20250803
Create Date: 2025-08-16

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '020_reset_database_clean'
down_revision = 'merge_heads_20250803'
branch_labels = None
depends_on = None


def upgrade():
    """Reset database with a clean schema"""
    # Get database connection and inspector
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    print(f"Found {len(existing_tables)} existing tables: {existing_tables}")
    
    # Drop all existing tables except alembic_version
    tables_to_drop = [table for table in existing_tables if table != 'alembic_version']
    
    for table in tables_to_drop:
        try:
            print(f"Dropping table: {table}")
            op.drop_table(table)
        except Exception as e:
            print(f"Error dropping table {table}: {e}")
    
    # Create clean schema based on current models
    
    # 1. Create accounts table first (referenced by other tables)
    print("Creating accounts table...")
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # 2. Create users table
    print("Creating users table...")
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='patient'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('account_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='SET NULL'),
    )
    
    # 3. Create patients table  
    print("Creating patients table...")
    op.create_table(
        'patients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=False),
        sa.Column('last_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(255), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(255), nullable=True, server_default='active'),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('emergency_contact_name', sa.String(255), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('clinician_id', sa.String(36), nullable=True),
        sa.Column('account_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.String(36), nullable=True, unique=True),
        sa.ForeignKeyConstraint(['clinician_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # 4. Create invites table
    print("Creating invites table...")
    op.create_table(
        'invites',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(32), nullable=True),
        sa.Column('invite_token', sa.String(64), nullable=False),
        sa.Column('clinician_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(32), nullable=True),
        sa.Column('custom_message', sa.Text(), nullable=True),
        sa.Column('session_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('chat_strategy', sa.String(100), nullable=True),
        sa.Column('patient_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinician_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # 5. Create AI chat tables
    print("Creating AI chat session tables...")
    op.create_table(
        'ai_chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('patient_id', sa.String(36), nullable=True),
        sa.Column('clinician_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('session_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinician_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    op.create_table(
        'ai_chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['ai_chat_sessions.id'], ondelete='CASCADE'),
    )
    
    # 6. Create chat strategy tables
    print("Creating chat strategy tables...")
    op.create_table(
        'chat_strategies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('account_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
    )
    
    op.create_table(
        'knowledge_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('account_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
    )
    
    # Add indexes
    print("Creating indexes...")
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_patients_email', 'patients', ['email'])
    op.create_index('ix_patients_external_id', 'patients', ['external_id'])
    op.create_index('ix_invites_email', 'invites', ['email'])
    op.create_index('ix_invites_invite_token', 'invites', ['invite_token'])
    
    print("✅ Clean database schema created successfully!")


def downgrade():
    """Drop all tables except alembic_version"""
    try:
        # Get all tables
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = inspector.get_table_names()
        
        # Drop all tables except alembic_version
        tables_to_drop = [table for table in existing_tables if table != 'alembic_version']
        
        for table in tables_to_drop:
            try:
                op.drop_table(table)
            except Exception as e:
                print(f"Error dropping table {table}: {e}")
        
        print("All tables dropped")
    except Exception as e:
        print(f"Error during downgrade: {e}")
