"""Add eligibility analysis tables

Revision ID: 004_eligibility_analysis
Revises: 003_invite_system
Create Date: 2025-05-08 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_eligibility_analysis'
down_revision = '003_invite_system'
branch_labels = None
depends_on = None

def upgrade():
    # Example: Create eligibility_results table
    op.create_table(
        'eligibility_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('patient_id', sa.String(36), nullable=False),
        sa.Column('result_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.Index('idx_eligibility_patient', 'patient_id'),
    )

def downgrade():
    op.drop_table('eligibility_results')
