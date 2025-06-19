"""merge_heads

Revision ID: b84fe9c40388
Revises: 012_chat_configuration_core, 47934cf19141, postgresql_conversion
Create Date: 2025-06-16 11:20:46.021599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b84fe9c40388'
down_revision: Union[str, None] = ('012_chat_configuration_core', '47934cf19141', 'postgresql_conversion')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
