"""Add missing columns to users table

Revision ID: 007_add_missing_user_columns
Revises: 001_initial_schema
Create Date: 2025-05-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_missing_user_columns'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255), nullable=False, unique=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('account_id', sa.String(36), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.add_column('users', sa.Column('clinician_id', sa.String(36), nullable=True))

def downgrade():
    op.drop_column('users', 'clinician_id')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'account_id')
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'email')
