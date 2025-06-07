"""Make patient_id non-nullable in invites table

Revision ID: 20250530_finalize_invites
Revises: c97a538f2456
Create Date: 2025-05-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250530_finalize_invites'
down_revision = 'c97a538f2456'
branch_labels = None
depends_on = None


def upgrade():
    # Make patient_id column non-nullable
    # Note: This should only be run after all existing invites have been migrated to link to patient records
    op.alter_column('invites', 'patient_id', nullable=False)


def downgrade():
    # Make patient_id column nullable again
    op.alter_column('invites', 'patient_id', nullable=True)
