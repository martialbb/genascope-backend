"""Add invite system tables

Revision ID: 003_invite_system
Revises: 002_chat_system
Create Date: 2025-05-05 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_invite_system'
down_revision = '002_chat_system'
branch_labels = None
depends_on = None

def upgrade():
    # Example: Create invites table (minimal for chain)
    op.create_table(
        'invites',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
    )

def downgrade():
    op.drop_table('invites')
