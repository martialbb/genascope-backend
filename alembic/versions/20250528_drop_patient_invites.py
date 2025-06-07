"""drop patient_invites table

Revision ID: 20250528_drop_patient_invites
Revises: 20250527_merge_multiple_heads
Create Date: 2025-05-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '20250528_drop_patient_invites'
down_revision: Union[str, None] = '20250527_merge_multiple_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Drop the patient_invites table as it's been replaced by invites.
    First, check if the table exists to avoid errors.
    """
    # Get connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if patient_invites table exists
    if 'patient_invites' in inspector.get_table_names():
        # Drop the table if it exists
        op.drop_table('patient_invites')


def downgrade() -> None:
    """
    No downgrade path as we've consolidated to invites table.
    The invites table already contains all needed data.
    """
    pass
