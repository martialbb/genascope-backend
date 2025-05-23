"""add session_type to chat_sessions

Revision ID: 11939f418bd8
Revises: d92192c739da
Create Date: 2025-05-22 05:29:23.371235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '11939f418bd8'
down_revision: Union[str, None] = 'd92192c739da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chat_sessions', sa.Column('session_type', sa.String(length=32), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chat_sessions', 'session_type')
