"""rename invite table to invites

Revision ID: 20250526_rename_invite_table
Revises: 72b453920928
Create Date: 2025-05-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250526_rename_invite_table'
down_revision: Union[str, None] = '72b453920928'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename the invite table to invites."""
    # Check if the old table exists, and rename it if it does
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'invite' in tables and 'invites' not in tables:
        op.rename_table('invite', 'invites')


def downgrade() -> None:
    """Rename the invites table back to invite."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'invites' in tables and 'invite' not in tables:
        op.rename_table('invites', 'invite')
