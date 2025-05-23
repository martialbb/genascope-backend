"""Merge heads

Revision ID: e3584a1531df
Revises: 006_appointments, 007_add_missing_user_columns
Create Date: 2025-05-22 04:29:15.262351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3584a1531df'
down_revision: Union[str, None] = ('006_appointments', '007_add_missing_user_columns')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
