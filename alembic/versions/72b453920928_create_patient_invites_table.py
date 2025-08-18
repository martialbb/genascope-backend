"""create invites table

Revision ID: 72b453920928
Revises: bcc9e2f6f6b4
Create Date: 2025-05-22 05:34:17.892843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '72b453920928'
down_revision: Union[str, None] = 'bcc9e2f6f6b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if invites table already exists before creating
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'invites' not in tables:
        op.create_table(
            'invites',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('first_name', sa.String(length=100), nullable=True),
            sa.Column('last_name', sa.String(length=100), nullable=True),
            sa.Column('phone', sa.String(length=32), nullable=True),
            sa.Column('invite_token', sa.String(length=64), nullable=False),
            sa.Column('clinician_id', sa.String(length=36), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=True),
            sa.Column('custom_message', sa.Text(), nullable=True),
            sa.Column('session_metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('accepted_at', sa.DateTime(), nullable=True),
        )
        print("✅ Created invites table")
    else:
        print("⚠️  Invites table already exists, skipping creation")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('invites')
