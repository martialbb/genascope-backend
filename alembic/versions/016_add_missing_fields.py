"""Add missing fields to chat configuration tables

Revision ID: 016_add_missing_fields
Revises: 015_add_account_id_columns
Create Date: 2025-07-04 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '016_add_missing_fields'
down_revision: Union[str, None] = '015_add_account_id_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing fields to chat configuration tables."""
    
    # Add missing columns to chat_strategies table
    op.add_column('chat_strategies', sa.Column('goal', sa.Text(), nullable=True))
    op.add_column('chat_strategies', sa.Column('patient_introduction', sa.Text(), nullable=True))
    op.add_column('chat_strategies', sa.Column('specialty', sa.String(100), nullable=True))
    
    # Add missing columns to knowledge_sources table
    op.add_column('knowledge_sources', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    """Remove missing fields from chat configuration tables."""
    op.drop_column('knowledge_sources', 'is_active')
    op.drop_column('chat_strategies', 'specialty')
    op.drop_column('chat_strategies', 'patient_introduction')
    op.drop_column('chat_strategies', 'goal')
