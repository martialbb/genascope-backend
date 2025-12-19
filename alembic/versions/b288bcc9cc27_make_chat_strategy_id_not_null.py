"""make_chat_strategy_id_not_null

Revision ID: b288bcc9cc27
Revises: 020_reset_database_clean
Create Date: 2025-12-18 22:32:08.285092

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b288bcc9cc27'
down_revision: Union[str, None] = '020_reset_database_clean'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make chat_strategy_id NOT NULL in invites table."""

    # Step 1: Update existing NULL values to a default chat strategy
    # Use 'strategy-1' (Genetic Counseling Assessment) as the default fallback
    op.execute("""
        UPDATE invites
        SET chat_strategy_id = 'strategy-1'
        WHERE chat_strategy_id IS NULL
    """)

    # Step 2: Alter the column to NOT NULL
    op.alter_column('invites', 'chat_strategy_id',
                    existing_type=sa.String(36),
                    nullable=False)


def downgrade() -> None:
    """Revert chat_strategy_id back to nullable."""

    # Alter the column back to nullable
    op.alter_column('invites', 'chat_strategy_id',
                    existing_type=sa.String(36),
                    nullable=True)
