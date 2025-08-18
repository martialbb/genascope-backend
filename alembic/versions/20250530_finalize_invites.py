"""Make patient_id non-nullable in invites table

Revision ID: 20250530_finalize_invites
Revises: c97a538f2456
Create Date: 2025-05-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20250530_finalize_invites'
down_revision = 'c97a538f2456'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection and inspector
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # Check if invites table exists
    if 'invites' not in inspector.get_table_names():
        print("⚠️  Invites table does not exist, skipping patient_id nullable constraint update")
        return
    
    # Check if patient_id column exists in invites table
    invites_columns = [col['name'] for col in inspector.get_columns('invites')]
    if 'patient_id' not in invites_columns:
        print("⚠️  Column patient_id does not exist in invites table, skipping nullable constraint update")
        return
    
    # Make patient_id column non-nullable
    # Note: This should only be run after all existing invites have been migrated to link to patient records
    print("✅ Making patient_id column non-nullable in invites table")
    op.alter_column('invites', 'patient_id', nullable=False)


def downgrade():
    # Get connection and inspector
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # Check if invites table exists
    if 'invites' not in inspector.get_table_names():
        print("⚠️  Invites table does not exist, skipping patient_id nullable constraint downgrade")
        return
    
    # Check if patient_id column exists in invites table
    invites_columns = [col['name'] for col in inspector.get_columns('invites')]
    if 'patient_id' not in invites_columns:
        print("⚠️  Column patient_id does not exist in invites table, skipping nullable constraint downgrade")
        return
    
    # Make patient_id column nullable again
    print("✅ Making patient_id column nullable in invites table")
    op.alter_column('invites', 'patient_id', nullable=True)
