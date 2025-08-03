"""add_simplified_access_tracking_to_invites

Revision ID: add_simplified_access_tracking
Revises: ce2d20f7e4be
Create Date: 2025-07-26 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_simplified_access_tracking'
down_revision = 'ce2d20f7e4be'
branch_labels = None
depends_on = None


def upgrade():
    """Add simplified access tracking columns to invites table"""
    # Add last_accessed column
    op.add_column('invites', sa.Column('last_accessed', sa.DateTime(), nullable=True))
    
    # Add access_count column
    op.add_column('invites', sa.Column('access_count', sa.Integer(), nullable=True, default=0))


def downgrade():
    """Remove simplified access tracking columns from invites table"""
    # Remove last_accessed column
    op.drop_column('invites', 'last_accessed')
    
    # Remove access_count column
    op.drop_column('invites', 'access_count')
