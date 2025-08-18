"""update invites table schema to match model

Revision ID: 20250527_update_invites_table
Revises: 20250526_merge_heads
Create Date: 2025-05-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20250527_update_invites_table'
down_revision: Union[str, None] = '20250526_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update the invites table schema to match our SQLAlchemy model."""
    # First check if the table structure needs to be updated
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('invites')]
    
    # Rename token to invite_token if needed
    if 'token' in columns and 'invite_token' not in columns:
        op.alter_column('invites', 'token', new_column_name='invite_token', existing_type=sa.String(64))
    
    # Add missing columns
    if 'user_id' not in columns:
        op.add_column('invites', sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True))
    
    if 'first_name' not in columns:
        op.add_column('invites', sa.Column('first_name', sa.String(255), nullable=True))
    
    if 'last_name' not in columns:
        op.add_column('invites', sa.Column('last_name', sa.String(255), nullable=True))
    
    if 'phone' not in columns:
        op.add_column('invites', sa.Column('phone', sa.String(20), nullable=True))
    
    if 'clinician_id' not in columns:
        op.add_column('invites', sa.Column('clinician_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True))
    
    if 'status' not in columns:
        op.add_column('invites', sa.Column('status', sa.String(20), nullable=True, server_default='pending'))
    
    if 'custom_message' not in columns:
        op.add_column('invites', sa.Column('custom_message', sa.Text, nullable=True))
    
    if 'session_metadata' not in columns:
        op.add_column('invites', sa.Column('session_metadata', sa.JSON, nullable=True))
    
    if 'expires_at' not in columns:
        op.add_column('invites', sa.Column('expires_at', sa.DateTime, nullable=True))
    
    if 'accepted_at' not in columns:
        op.add_column('invites', sa.Column('accepted_at', sa.DateTime, nullable=True))

    # Update nullable constraints after data migration
    try:
        # Try to make columns non-nullable only if they exist
        if 'first_name' in columns or 'first_name' in [col['name'] for col in inspector.get_columns('invites')]:
            op.alter_column('invites', 'first_name', existing_type=sa.String(255), nullable=False)
        
        if 'last_name' in columns or 'last_name' in [col['name'] for col in inspector.get_columns('invites')]:
            op.alter_column('invites', 'last_name', existing_type=sa.String(255), nullable=False)
        
        if 'clinician_id' in columns or 'clinician_id' in [col['name'] for col in inspector.get_columns('invites')]:
            op.alter_column('invites', 'clinician_id', existing_type=sa.String(36), nullable=False)
        
        if 'status' in columns or 'status' in [col['name'] for col in inspector.get_columns('invites')]:
            op.alter_column('invites', 'status', existing_type=sa.String(20), nullable=False)
        
        if 'expires_at' in columns or 'expires_at' in [col['name'] for col in inspector.get_columns('invites')]:
            op.alter_column('invites', 'expires_at', existing_type=sa.DateTime, nullable=False)
    except Exception as e:
        # Log error but continue with migration
        print(f"Warning: Failed to set non-nullable constraints: {str(e)}")
    
    # Create necessary indexes (only if they don't exist)
    try:
        connection = op.get_bind()
        
        # Check if ix_invites_email index exists
        result = connection.execute(sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname = 'ix_invites_email'"
        )).fetchone()
        
        if not result:
            op.create_index(op.f('ix_invites_email'), 'invites', ['email'], unique=False)
            print("✅ Created index: ix_invites_email")
        else:
            print("⚠️  Index ix_invites_email already exists, skipping")
        
        # Check if ix_invites_invite_token index exists
        result = connection.execute(sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname = 'ix_invites_invite_token'"
        )).fetchone()
        
        if not result:
            op.create_index(op.f('ix_invites_invite_token'), 'invites', ['invite_token'], unique=True)
            print("✅ Created index: ix_invites_invite_token")
        else:
            print("⚠️  Index ix_invites_invite_token already exists, skipping")
            
    except Exception as e:
        # Log error but continue with migration
        print(f"Warning: Failed to create indexes: {str(e)}")


def downgrade() -> None:
    """This downgrade is intentionally simple to avoid data loss."""
    # We'll only drop the new columns
    op.drop_column('invites', 'user_id')
    op.drop_column('invites', 'first_name')
    op.drop_column('invites', 'last_name')
    op.drop_column('invites', 'phone')
    op.drop_column('invites', 'clinician_id')
    op.drop_column('invites', 'status')
    op.drop_column('invites', 'custom_message')
    op.drop_column('invites', 'session_metadata')
    op.drop_column('invites', 'expires_at')
    op.drop_column('invites', 'accepted_at')
    
    # Revert invite_token back to token if we renamed it
    op.alter_column('invites', 'invite_token', new_column_name='token', existing_type=sa.String(64))
