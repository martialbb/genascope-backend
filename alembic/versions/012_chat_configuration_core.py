"""Chat Configuration System - Core Models

Revision ID: 012_chat_configuration_core
Revises: 011_add_time_and_end_date
Create Date: 2025-06-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_chat_configuration_core'
down_revision = '011_add_time_and_end_date'
branch_labels = None
depends_on = None


def upgrade():
    # Create chat_strategies table
    op.create_table(
        'chat_strategies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('patient_introduction', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
        sa.Column('specialty', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create knowledge_sources table
    op.create_table(
        'knowledge_sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_size', sa.String(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=True),
        sa.Column('uploaded_by', sa.String(), nullable=True),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create strategy_knowledge_sources junction table
    op.create_table(
        'strategy_knowledge_sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('knowledge_source_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_source_id'], ['knowledge_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_id', 'knowledge_source_id')
    )

    # Create targeting_rules table
    op.create_table(
        'targeting_rules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('field', sa.String(), nullable=False),
        sa.Column('operator', sa.String(), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create outcome_actions table
    op.create_table(
        'outcome_actions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create strategy_executions table
    op.create_table(
        'strategy_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('triggered_by', sa.String(), nullable=True),
        sa.Column('trigger_criteria', postgresql.JSONB(), nullable=True),
        sa.Column('execution_status', sa.String(), nullable=False, default='in_progress'),
        sa.Column('outcome_result', sa.String(), nullable=True),
        sa.Column('executed_actions', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create strategy_analytics table
    op.create_table(
        'strategy_analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('patients_screened', sa.Integer(), nullable=False, default=0),
        sa.Column('criteria_met', sa.Integer(), nullable=False, default=0),
        sa.Column('criteria_not_met', sa.Integer(), nullable=False, default=0),
        sa.Column('incomplete_data', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('tasks_created', sa.Integer(), nullable=False, default=0),
        sa.Column('charts_flagged', sa.Integer(), nullable=False, default=0),
        sa.Column('messages_sent', sa.Integer(), nullable=False, default=0),
        sa.Column('followups_scheduled', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_id', 'date')
    )

    # Add columns to existing chat_sessions table
    op.add_column('chat_sessions', sa.Column('strategy_id', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('strategy_execution_id', sa.String(), nullable=True))
    op.add_column('chat_sessions', sa.Column('triggered_by_rules', postgresql.JSONB(), nullable=True))
    
    # Add foreign key constraints for new columns
    op.create_foreign_key(
        'fk_chat_sessions_strategy_id', 'chat_sessions', 'chat_strategies',
        ['strategy_id'], ['id']
    )
    op.create_foreign_key(
        'fk_chat_sessions_strategy_execution_id', 'chat_sessions', 'strategy_executions',
        ['strategy_execution_id'], ['id']
    )

    # Add columns to existing chat_questions table
    op.add_column('chat_questions', sa.Column('strategy_id', sa.String(), nullable=True))
    op.add_column('chat_questions', sa.Column('knowledge_source_id', sa.String(), nullable=True))
    op.add_column('chat_questions', sa.Column('is_dynamic', sa.Boolean(), nullable=False, default=False))
    op.add_column('chat_questions', sa.Column('context', postgresql.JSONB(), nullable=True))
    
    # Add foreign key constraints for new columns
    op.create_foreign_key(
        'fk_chat_questions_strategy_id', 'chat_questions', 'chat_strategies',
        ['strategy_id'], ['id']
    )
    op.create_foreign_key(
        'fk_chat_questions_knowledge_source_id', 'chat_questions', 'knowledge_sources',
        ['knowledge_source_id'], ['id']
    )

    # Create indexes for performance
    op.create_index('idx_chat_strategies_account_id', 'chat_strategies', ['account_id'])
    op.create_index('idx_chat_strategies_is_active', 'chat_strategies', ['is_active'])
    op.create_index('idx_knowledge_sources_account_id', 'knowledge_sources', ['account_id'])
    op.create_index('idx_knowledge_sources_type', 'knowledge_sources', ['type'])
    op.create_index('idx_targeting_rules_strategy_id', 'targeting_rules', ['strategy_id'])
    op.create_index('idx_outcome_actions_strategy_id', 'outcome_actions', ['strategy_id'])
    op.create_index('idx_strategy_executions_strategy_id', 'strategy_executions', ['strategy_id'])
    op.create_index('idx_strategy_executions_patient_id', 'strategy_executions', ['patient_id'])
    op.create_index('idx_strategy_analytics_strategy_id', 'strategy_analytics', ['strategy_id'])
    op.create_index('idx_strategy_analytics_date', 'strategy_analytics', ['date'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_strategy_analytics_date', table_name='strategy_analytics')
    op.drop_index('idx_strategy_analytics_strategy_id', table_name='strategy_analytics')
    op.drop_index('idx_strategy_executions_patient_id', table_name='strategy_executions')
    op.drop_index('idx_strategy_executions_strategy_id', table_name='strategy_executions')
    op.drop_index('idx_outcome_actions_strategy_id', table_name='outcome_actions')
    op.drop_index('idx_targeting_rules_strategy_id', table_name='targeting_rules')
    op.drop_index('idx_knowledge_sources_type', table_name='knowledge_sources')
    op.drop_index('idx_knowledge_sources_account_id', table_name='knowledge_sources')
    op.drop_index('idx_chat_strategies_is_active', table_name='chat_strategies')
    op.drop_index('idx_chat_strategies_account_id', table_name='chat_strategies')

    # Drop foreign key constraints and columns from existing tables
    op.drop_constraint('fk_chat_questions_knowledge_source_id', 'chat_questions', type_='foreignkey')
    op.drop_constraint('fk_chat_questions_strategy_id', 'chat_questions', type_='foreignkey')
    op.drop_column('chat_questions', 'context')
    op.drop_column('chat_questions', 'is_dynamic')
    op.drop_column('chat_questions', 'knowledge_source_id')
    op.drop_column('chat_questions', 'strategy_id')

    op.drop_constraint('fk_chat_sessions_strategy_execution_id', 'chat_sessions', type_='foreignkey')
    op.drop_constraint('fk_chat_sessions_strategy_id', 'chat_sessions', type_='foreignkey')
    op.drop_column('chat_sessions', 'triggered_by_rules')
    op.drop_column('chat_sessions', 'strategy_execution_id')
    op.drop_column('chat_sessions', 'strategy_id')

    # Drop new tables
    op.drop_table('strategy_analytics')
    op.drop_table('strategy_executions')
    op.drop_table('outcome_actions')
    op.drop_table('targeting_rules')
    op.drop_table('strategy_knowledge_sources')
    op.drop_table('knowledge_sources')
    op.drop_table('chat_strategies')
