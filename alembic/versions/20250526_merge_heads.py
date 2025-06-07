"""merge multiple heads

Revision ID: 20250526_merge_heads
Revises: 011_add_time_and_end_date, 20250526_rename_invite_table
Create Date: 2025-05-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250526_merge_heads'
down_revision = ('011_add_time_and_end_date', '20250526_rename_invite_table')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is an empty migration that just merges heads
    pass


def downgrade() -> None:
    # This is an empty migration that just merges heads
    pass
