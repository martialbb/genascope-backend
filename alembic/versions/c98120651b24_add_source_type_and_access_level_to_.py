"""Add source_type and access_level to knowledge_sources

Revision ID: c98120651b24
Revises: 91322dac4cb2
Create Date: 2025-07-05 00:23:51.555042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c98120651b24'
down_revision: Union[str, None] = 'b2d62cbf263a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add source_type and access_level columns to knowledge_sources table."""
    
    # Add missing columns to knowledge_sources table
    op.add_column('knowledge_sources', sa.Column('source_type', sa.String(50), nullable=False, server_default='custom_document'))
    op.add_column('knowledge_sources', sa.Column('access_level', sa.String(50), nullable=False, server_default='public'))


def downgrade() -> None:
    """Remove source_type and access_level columns from knowledge_sources table."""
    op.drop_column('knowledge_sources', 'access_level')
    op.drop_column('knowledge_sources', 'source_type')
