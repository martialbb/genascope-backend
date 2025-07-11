"""merge_heads

Revision ID: 663cd5e819c6
Revises: ce2d20f7e4be, 014_document_chunks_pgvector
Create Date: 2025-07-03 09:42:21.665429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '663cd5e819c6'
down_revision: Union[str, None] = ('ce2d20f7e4be', '014_document_chunks_pgvector')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
