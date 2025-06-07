"""add_patient_profiles

Revision ID: b86a120f1234
Revises: 20250528_drop_patient_invites
Create Date: 2025-05-28

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'b86a120f1234'
down_revision = '20250528_drop_patient_invites'
branch_labels = None
depends_on = None


def upgrade():
    # Create patient_profiles table based on the PatientProfile model
    op.create_table(
        'patient_profiles',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('date_of_birth', sa.DateTime(), nullable=True),
        sa.Column('gender', sa.String(length=50), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('medical_history', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('user_id')
    )
    # Add index on user_id for faster lookups
    op.create_index(op.f('ix_patient_profiles_user_id'), 'patient_profiles', ['user_id'], unique=True)


def downgrade():
    # Drop the patient_profiles table
    op.drop_index(op.f('ix_patient_profiles_user_id'), table_name='patient_profiles')
    op.drop_table('patient_profiles')
