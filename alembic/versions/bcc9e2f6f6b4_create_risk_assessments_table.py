"""create risk_assessments table

Revision ID: bcc9e2f6f6b4
Revises: 008a612b804d
Create Date: 2025-05-22 05:32:59.372932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'bcc9e2f6f6b4'
down_revision: Union[str, None] = '008a612b804d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('is_eligible', sa.Boolean(), nullable=True),
        sa.Column('nccn_eligible', sa.Boolean(), nullable=True),
        sa.Column('tyrer_cuzick_score', sa.Float(), nullable=True),
        sa.Column('tyrer_cuzick_threshold', sa.Float(), nullable=True),
        sa.Column('risk_factors', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('risk_assessments')
