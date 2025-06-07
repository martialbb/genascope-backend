"""merge_migration_heads

Revision ID: b9f17e376544
Revises: 20250526_merge_heads
Create Date: 2025-05-26 06:16:15.169474

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9f17e376544'
down_revision: Union[str, None] = '20250526_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
