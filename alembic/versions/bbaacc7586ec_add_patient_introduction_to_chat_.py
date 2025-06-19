"""add_patient_introduction_to_chat_strategies

Revision ID: bbaacc7586ec
Revises: 6dcbfeb0a5ea
Create Date: 2025-06-16 21:46:03.038602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbaacc7586ec'
down_revision: Union[str, None] = '6dcbfeb0a5ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing columns to chat_strategies table
    op.add_column('chat_strategies', sa.Column('patient_introduction', sa.Text(), nullable=True))
    op.add_column('chat_strategies', sa.Column('specialty', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove added columns
    op.drop_column('chat_strategies', 'specialty')
    op.drop_column('chat_strategies', 'patient_introduction')
