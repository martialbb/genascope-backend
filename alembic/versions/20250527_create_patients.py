"""Create patients table

Revision ID: 20250527_create_patients
Revises: 72b453920928
Create Date: 2025-05-27

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20250527_create_patients'
down_revision = '72b453920928'
branch_labels = None
depends_on = None


def upgrade():
    # Check if patients table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'patients' not in inspector.get_table_names():
        print("Creating patients table...")
        # Create patients table
        op.create_table(
            'patients',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('email', sa.String(255), nullable=False, index=True),
            sa.Column('first_name', sa.String(100), nullable=False),
            sa.Column('last_name', sa.String(100), nullable=False),
            sa.Column('phone', sa.String(20), nullable=True),
            sa.Column('external_id', sa.String(100), nullable=True, index=True),
            sa.Column('date_of_birth', sa.Date(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, 
                      server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('clinician_id', sa.String(36), nullable=True),
            sa.Column('account_id', sa.String(36), nullable=True),
            
            # Foreign keys
            sa.ForeignKeyConstraint(['clinician_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='SET NULL'),
        )
        print("Patients table created successfully")
    else:
        print("Patients table already exists, skipping...")
    
    # Add indexes for better performance if they don't exist
    try:
        indexes = inspector.get_indexes('patients') if 'patients' in inspector.get_table_names() else []
        existing_indexes = [idx['name'] for idx in indexes]
        
        if 'ix_patients_email' not in existing_indexes:
            op.create_index(op.f('ix_patients_email'), 'patients', ['email'])
            print("Created ix_patients_email index")
        else:
            print("ix_patients_email index already exists")
            
        if 'ix_patients_external_id' not in existing_indexes:
            op.create_index(op.f('ix_patients_external_id'), 'patients', ['external_id'])
            print("Created ix_patients_external_id index")
        else:
            print("ix_patients_external_id index already exists")
    except Exception as e:
        print(f"Error checking/creating indexes: {e}")


def downgrade():
    # Drop patients table safely
    try:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        
        if 'patients' in inspector.get_table_names():
            # Drop indexes first
            try:
                indexes = inspector.get_indexes('patients')
                existing_indexes = [idx['name'] for idx in indexes]
                
                if 'ix_patients_external_id' in existing_indexes:
                    op.drop_index(op.f('ix_patients_external_id'), 'patients')
                if 'ix_patients_email' in existing_indexes:
                    op.drop_index(op.f('ix_patients_email'), 'patients')
            except Exception as e:
                print(f"Error dropping indexes: {e}")
            
            # Drop table
            op.drop_table('patients')
            print("Patients table dropped successfully")
        else:
            print("Patients table does not exist, skipping...")
    except Exception as e:
        print(f"Error during downgrade: {e}")
