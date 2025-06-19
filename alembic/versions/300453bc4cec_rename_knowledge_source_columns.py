"""rename_knowledge_source_columns

Revision ID: 300453bc4cec
Revises: bbaacc7586ec
Create Date: 2025-06-16 22:36:37.319024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '300453bc4cec'
down_revision: Union[str, None] = 'bbaacc7586ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename columns to match current model
    op.alter_column('knowledge_sources', 'name', new_column_name='title')
    op.alter_column('knowledge_sources', 'source_type', new_column_name='type')
    
    # Add missing columns that the model expects
    op.add_column('knowledge_sources', sa.Column('url', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('storage_type', sa.String(), nullable=False, server_default='s3'))
    op.add_column('knowledge_sources', sa.Column('storage_provider', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('s3_region', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('s3_endpoint', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('file_name', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('file_extension', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('file_size_bytes', sa.Integer(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('file_checksum', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('file_encryption_key', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('extracted_text', sa.Text(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('content_sections', sa.JSON(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('search_vector', sa.Text(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('ai_insights', sa.JSON(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('version', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('category', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('specialty', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('tags', sa.JSON(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('keywords', sa.JSON(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('processing_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('knowledge_sources', sa.Column('content_extracted_at', sa.DateTime(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('last_accessed_at', sa.DateTime(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('upload_date', sa.DateTime(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('uploaded_by', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('knowledge_sources', sa.Column('retention_policy', sa.String(), nullable=True))
    op.add_column('knowledge_sources', sa.Column('archived_at', sa.DateTime(), nullable=True))
    
    # Rename existing columns
    op.alter_column('knowledge_sources', 'file_size', new_column_name='file_size_legacy')
    op.alter_column('knowledge_sources', 'file_path', new_column_name='file_path_legacy')
    op.alter_column('knowledge_sources', 's3_url', new_column_name='s3_url_legacy')
    op.alter_column('knowledge_sources', 'metadata', new_column_name='metadata_legacy')
    op.alter_column('knowledge_sources', 'created_by', new_column_name='uploaded_by_legacy')


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse all changes
    op.alter_column('knowledge_sources', 'title', new_column_name='name')
    op.alter_column('knowledge_sources', 'type', new_column_name='source_type')
    
    # Drop added columns
    op.drop_column('knowledge_sources', 'archived_at')
    op.drop_column('knowledge_sources', 'retention_policy')
    op.drop_column('knowledge_sources', 'is_public')
    op.drop_column('knowledge_sources', 'uploaded_by')
    op.drop_column('knowledge_sources', 'upload_date')
    op.drop_column('knowledge_sources', 'last_accessed_at')
    op.drop_column('knowledge_sources', 'content_extracted_at')
    op.drop_column('knowledge_sources', 'processing_attempts')
    op.drop_column('knowledge_sources', 'keywords')
    op.drop_column('knowledge_sources', 'tags')
    op.drop_column('knowledge_sources', 'specialty')
    op.drop_column('knowledge_sources', 'category')
    op.drop_column('knowledge_sources', 'version')
    op.drop_column('knowledge_sources', 'ai_insights')
    op.drop_column('knowledge_sources', 'search_vector')
    op.drop_column('knowledge_sources', 'content_sections')
    op.drop_column('knowledge_sources', 'extracted_text')
    op.drop_column('knowledge_sources', 'file_encryption_key')
    op.drop_column('knowledge_sources', 'file_checksum')
    op.drop_column('knowledge_sources', 'file_size_bytes')
    op.drop_column('knowledge_sources', 'file_extension')
    op.drop_column('knowledge_sources', 'file_name')
    op.drop_column('knowledge_sources', 's3_endpoint')
    op.drop_column('knowledge_sources', 's3_region')
    op.drop_column('knowledge_sources', 'storage_provider')
    op.drop_column('knowledge_sources', 'storage_type')
    op.drop_column('knowledge_sources', 'url')
    
    # Restore original columns
    op.alter_column('knowledge_sources', 'file_size_legacy', new_column_name='file_size')
    op.alter_column('knowledge_sources', 'file_path_legacy', new_column_name='file_path')
    op.alter_column('knowledge_sources', 's3_url_legacy', new_column_name='s3_url')
    op.alter_column('knowledge_sources', 'metadata_legacy', new_column_name='metadata')
    op.alter_column('knowledge_sources', 'uploaded_by_legacy', new_column_name='created_by')
