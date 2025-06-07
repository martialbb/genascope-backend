"""merge_multiple_heads

Revision ID: 20250527_merge_multiple_heads
Revises: 20250527_update_invites_table, b9f17e376544
Create Date: 2025-05-27 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250527_merge_multiple_heads'
down_revision: Union[str, None] = ('20250527_update_invites_table', 'b9f17e376544')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is an empty migration that just merges heads
    pass


def downgrade() -> None:
    # This is an empty migration that just merges heads
    pass
