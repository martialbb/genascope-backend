"""add_chat_strategy_to_invites

Revision ID: add_chat_strategy_to_invites
Revises: add_simplified_access_tracking
Create Date: 2025-08-01 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_chat_strategy_to_invites'
down_revision = '9ded4b6ea794'
branch_labels = None
depends_on = None


def upgrade():
    """Add chat_strategy_id column to invites table"""
    # Add chat_strategy_id column (nullable initially to handle existing data)
    op.add_column('invites', sa.Column('chat_strategy_id', sa.String(36), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_invites_chat_strategy_id',
        'invites', 'chat_strategies',
        ['chat_strategy_id'], ['id']
    )


def downgrade():
    """Remove chat_strategy_id column from invites table"""
    # Drop foreign key constraint
    op.drop_constraint('fk_invites_chat_strategy_id', 'invites', type_='foreignkey')
    
    # Remove chat_strategy_id column
    op.drop_column('invites', 'chat_strategy_id')
