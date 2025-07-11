"""Add AI chat session models

Revision ID: 013_ai_chat_sessions
Revises: 012_chat_configuration_core
Create Date: 2025-06-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_ai_chat_sessions'
down_revision = '012_chat_configuration_core'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE sessiontype AS ENUM ('screening', 'assessment', 'follow_up', 'consultation')")
    op.execute("CREATE TYPE sessionstatus AS ENUM ('active', 'completed', 'paused', 'error', 'cancelled')")
    op.execute("CREATE TYPE messagerole AS ENUM ('user', 'assistant', 'system')")
    op.execute("CREATE TYPE messagetype AS ENUM ('question', 'response', 'summary', 'assessment', 'clarification')")
    op.execute("CREATE TYPE extractionmethod AS ENUM ('llm', 'regex', 'ner', 'hybrid')")

    # Create ai_chat_sessions table
    op.create_table('ai_chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_type', postgresql.ENUM('screening', 'assessment', 'follow_up', 'consultation', name='sessiontype'), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'completed', 'paused', 'error', 'cancelled', name='sessionstatus'), nullable=False),
        sa.Column('chat_context', sa.JSON(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('assessment_results', sa.JSON(), nullable=True),
        sa.Column('strategy_snapshot', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_chat_sessions_patient_id'), 'ai_chat_sessions', ['patient_id'], unique=False)
    op.create_index(op.f('ix_ai_chat_sessions_strategy_id'), 'ai_chat_sessions', ['strategy_id'], unique=False)
    op.create_index(op.f('ix_ai_chat_sessions_status'), 'ai_chat_sessions', ['status'], unique=False)
    op.create_index(op.f('ix_ai_chat_sessions_started_at'), 'ai_chat_sessions', ['started_at'], unique=False)

    # Create ai_chat_messages table
    op.create_table('ai_chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', postgresql.ENUM('user', 'assistant', 'system', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', postgresql.ENUM('question', 'response', 'summary', 'assessment', 'clarification', name='messagetype'), nullable=False),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('rag_sources', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extracted_entities', sa.JSON(), nullable=True),
        sa.Column('extracted_intent', sa.String(100), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['ai_chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_chat_messages_session_id'), 'ai_chat_messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_ai_chat_messages_role'), 'ai_chat_messages', ['role'], unique=False)
    op.create_index(op.f('ix_ai_chat_messages_created_at'), 'ai_chat_messages', ['created_at'], unique=False)

    # Create ai_extraction_rules table
    op.create_table('ai_extraction_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('extraction_method', postgresql.ENUM('llm', 'regex', 'ner', 'hybrid', name='extractionmethod'), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=True),
        sa.Column('validation_rules', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=1),
        sa.Column('trigger_conditions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_extraction_rules_strategy_id'), 'ai_extraction_rules', ['strategy_id'], unique=False)
    op.create_index(op.f('ix_ai_extraction_rules_entity_type'), 'ai_extraction_rules', ['entity_type'], unique=False)

    # Create ai_session_analytics table for tracking metrics
    op.create_table('ai_session_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_messages', sa.Integer(), nullable=False, default=0),
        sa.Column('conversation_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('extraction_accuracy', sa.Float(), nullable=True),
        sa.Column('patient_satisfaction_score', sa.Float(), nullable=True),
        sa.Column('ai_confidence_avg', sa.Float(), nullable=True),
        sa.Column('criteria_met', sa.Boolean(), nullable=True),
        sa.Column('recommendations_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['ai_chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_session_analytics_session_id'), 'ai_session_analytics', ['session_id'], unique=False)

    # Add AI-related columns to chat_strategies table
    op.add_column('chat_strategies', sa.Column('ai_model_config', sa.JSON(), nullable=True))
    op.add_column('chat_strategies', sa.Column('rag_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('chat_strategies', sa.Column('extraction_rules_config', sa.JSON(), nullable=True))
    op.add_column('chat_strategies', sa.Column('assessment_criteria', sa.JSON(), nullable=True))
    op.add_column('chat_strategies', sa.Column('required_information', sa.JSON(), nullable=True))
    op.add_column('chat_strategies', sa.Column('max_conversation_turns', sa.Integer(), nullable=True, server_default='20'))


def downgrade() -> None:
    # Remove columns from chat_strategies
    op.drop_column('chat_strategies', 'max_conversation_turns')
    op.drop_column('chat_strategies', 'required_information')
    op.drop_column('chat_strategies', 'assessment_criteria')
    op.drop_column('chat_strategies', 'extraction_rules_config')
    op.drop_column('chat_strategies', 'rag_enabled')
    op.drop_column('chat_strategies', 'ai_model_config')

    # Drop tables
    op.drop_index(op.f('ix_ai_session_analytics_session_id'), table_name='ai_session_analytics')
    op.drop_table('ai_session_analytics')

    op.drop_index(op.f('ix_ai_extraction_rules_entity_type'), table_name='ai_extraction_rules')
    op.drop_index(op.f('ix_ai_extraction_rules_strategy_id'), table_name='ai_extraction_rules')
    op.drop_table('ai_extraction_rules')

    op.drop_index(op.f('ix_ai_chat_messages_created_at'), table_name='ai_chat_messages')
    op.drop_index(op.f('ix_ai_chat_messages_role'), table_name='ai_chat_messages')
    op.drop_index(op.f('ix_ai_chat_messages_session_id'), table_name='ai_chat_messages')
    op.drop_table('ai_chat_messages')

    op.drop_index(op.f('ix_ai_chat_sessions_started_at'), table_name='ai_chat_sessions')
    op.drop_index(op.f('ix_ai_chat_sessions_status'), table_name='ai_chat_sessions')
    op.drop_index(op.f('ix_ai_chat_sessions_strategy_id'), table_name='ai_chat_sessions')
    op.drop_index(op.f('ix_ai_chat_sessions_patient_id'), table_name='ai_chat_sessions')
    op.drop_table('ai_chat_sessions')

    # Drop enum types
    op.execute("DROP TYPE extractionmethod")
    op.execute("DROP TYPE messagetype")
    op.execute("DROP TYPE messagerole")
    op.execute("DROP TYPE sessionstatus")
    op.execute("DROP TYPE sessiontype")
