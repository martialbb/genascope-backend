"""Add created_by and version fields to chat_strategies

Revision ID: b2d62cbf263a
Revises: 016_add_missing_fields
Create Date: 2025-07-05 00:16:10.642270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d62cbf263a'
down_revision: Union[str, None] = '016_add_missing_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add created_by and version fields to chat_strategies table."""
    
    # Add missing columns to chat_strategies table
    op.add_column('chat_strategies', sa.Column('created_by', sa.String(36), nullable=True))
    op.add_column('chat_strategies', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    """Remove created_by and version fields from chat_strategies table."""
    op.drop_column('chat_strategies', 'version')
    op.drop_column('chat_strategies', 'created_by')
