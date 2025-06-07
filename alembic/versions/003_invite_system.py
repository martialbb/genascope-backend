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
    # Create invites table with all required fields
    op.create_table(
        'invites',  # Match the actual table name in the database
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('first_name', sa.String(255), nullable=False),
        sa.Column('last_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(255), nullable=True),
        sa.Column('invite_token', sa.String(64), nullable=False, unique=True),
        sa.Column('clinician_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('custom_message', sa.Text, nullable=True),
        sa.Column('session_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True)
    )

def downgrade():
    op.drop_table('invites')
