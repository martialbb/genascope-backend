"""merge_chat_strategy_and_access_tracking

Revision ID: merge_heads_20250803
Revises: add_chat_strategy_to_invites, add_simplified_access_tracking
Create Date: 2025-08-03 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_20250803'
down_revision = ('add_chat_strategy_to_invites', 'add_simplified_access_tracking')
branch_labels = None
depends_on = None


def upgrade():
    """Merge the chat strategy and access tracking migrations"""
    # No operations needed - this is just a merge point
    pass


def downgrade():
    """Downgrade the merge"""
    # No operations needed - this is just a merge point
    pass
