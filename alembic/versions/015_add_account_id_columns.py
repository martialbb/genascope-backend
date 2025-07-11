"""Add account_id to chat configuration tables

Revision ID: 015_add_account_id_columns
Revises: 014_chat_config_complete
Create Date: 2025-07-04 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '015_add_account_id_columns'
down_revision: Union[str, None] = '014_chat_config_complete'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add account_id columns to chat configuration tables."""
    
    # Add account_id to chat_strategies table
    op.add_column('chat_strategies', sa.Column('account_id', sa.String(36), nullable=True))
    op.create_foreign_key('fk_chat_strategies_account', 'chat_strategies', 'accounts', ['account_id'], ['id'])
    
    # Add account_id to knowledge_sources table
    op.add_column('knowledge_sources', sa.Column('account_id', sa.String(36), nullable=True))
    op.create_foreign_key('fk_knowledge_sources_account', 'knowledge_sources', 'accounts', ['account_id'], ['id'])
    
    # Set default account_id for existing records (use first account if available)
    op.execute("""
        UPDATE chat_strategies 
        SET account_id = (SELECT id FROM accounts LIMIT 1) 
        WHERE account_id IS NULL
    """)
    
    op.execute("""
        UPDATE knowledge_sources 
        SET account_id = (SELECT id FROM accounts LIMIT 1) 
        WHERE account_id IS NULL
    """)
    
    # Make account_id NOT NULL after setting defaults
    op.alter_column('chat_strategies', 'account_id', nullable=False)
    op.alter_column('knowledge_sources', 'account_id', nullable=False)


def downgrade() -> None:
    """Remove account_id columns from chat configuration tables."""
    op.drop_constraint('fk_chat_strategies_account', 'chat_strategies', type_='foreignkey')
    op.drop_column('chat_strategies', 'account_id')
    
    op.drop_constraint('fk_knowledge_sources_account', 'knowledge_sources', type_='foreignkey')
    op.drop_column('knowledge_sources', 'account_id')
