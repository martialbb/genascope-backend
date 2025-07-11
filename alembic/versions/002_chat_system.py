"""Add chat system tables

Revision ID: 002_chat_system
Revises: 001_initial_schema
Create Date: 2025-05-03 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_chat_system'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Example: Create chat_sessions table (minimal for chain)
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade():
    op.drop_table('chat_sessions')
