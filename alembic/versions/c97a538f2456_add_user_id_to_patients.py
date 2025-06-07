"""Add user_id to patients table

Revision ID: c97a538f2456
Revises: b86a120f1234
Create Date: 2025-05-29

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c97a538f2456'
down_revision = 'b86a120f1234'
branch_labels = None
depends_on = None


def upgrade():
    # Add user_id column to patients table
    op.add_column('patients', sa.Column('user_id', sa.String(36), nullable=True))
    
    # Add unique constraint and foreign key constraint
    op.create_unique_constraint('uq_patients_user_id', 'patients', ['user_id'])
    op.create_foreign_key(
        'fk_patients_user_id', 'patients', 'users',
        ['user_id'], ['id'], ondelete='SET NULL'
    )


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_patients_user_id', 'patients', type_='foreignkey')
    
    # Remove unique constraint
    op.drop_constraint('uq_patients_user_id', 'patients', type_='unique')
    
    # Remove user_id column
    op.drop_column('patients', 'user_id')
