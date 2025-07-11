"""add document chunks with pgvector

Revision ID: 014_document_chunks_pgvector
Revises: 013_ai_chat_sessions
Create Date: 2025-07-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = '014_document_chunks_pgvector'
down_revision = '013_ai_chat_sessions'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('knowledge_source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['knowledge_source_id'], ['knowledge_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create standard indexes
    op.create_index('ix_document_chunks_knowledge_source', 'document_chunks', ['knowledge_source_id'])
    op.create_index('ix_document_chunks_created_at', 'document_chunks', ['created_at'])
    op.create_index('ix_document_chunks_chunk_index', 'document_chunks', ['chunk_index'])
    
    # Create full-text search index
    op.execute("""
        CREATE INDEX ix_document_chunks_content_fts 
        ON document_chunks USING gin (to_tsvector('english', content))
    """)
    
    # Create vector similarity index (ivfflat for cosine similarity)
    # Note: This requires data in the table, so we'll create a basic index first
    op.execute("""
        CREATE INDEX ix_document_chunks_embedding_cosine 
        ON document_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)
    
    # Create trigger for updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    
    op.execute("""
        CREATE TRIGGER update_document_chunks_updated_at 
        BEFORE UPDATE ON document_chunks 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON document_chunks")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop table (indexes will be dropped automatically)
    op.drop_table('document_chunks')
