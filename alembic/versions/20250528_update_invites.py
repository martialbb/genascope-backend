"""Update invite table to add patient_id

Revision ID: 20250528_update_invites
Revises: 20250527_create_patients
Create Date: 2025-05-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20250528_update_invites'
down_revision = '20250527_create_patients'
branch_labels = None
depends_on = None


def upgrade():
    # Add patient_id column to invites table
    op.add_column('invites', sa.Column('patient_id', sa.String(36), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_invites_patient_id', 'invites', 'patients',
        ['patient_id'], ['id'], ondelete='CASCADE'
    )
    
    # Initially set to nullable to avoid breaking existing records,
    # but in production systems we would migrate the existing data first
    # before making it non-nullable


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_invites_patient_id', 'invites', type_='foreignkey')
    
    # Remove patient_id column
    op.drop_column('invites', 'patient_id')
