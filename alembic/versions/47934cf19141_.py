"""empty message

Revision ID: 47934cf19141
Revises: 20250528_update_invites, 20250530_finalize_invites
Create Date: 2025-05-28 07:25:50.170483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47934cf19141'
down_revision: Union[str, None] = ('20250528_update_invites', '20250530_finalize_invites')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
