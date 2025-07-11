"""Merge migration heads

Revision ID: 9ded4b6ea794
Revises: 91322dac4cb2, c98120651b24
Create Date: 2025-07-05 00:30:58.001249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ded4b6ea794'
down_revision: Union[str, None] = ('91322dac4cb2', 'c98120651b24')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
