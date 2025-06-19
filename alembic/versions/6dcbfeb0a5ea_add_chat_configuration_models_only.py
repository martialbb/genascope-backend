"""add_chat_configuration_models_only

Revision ID: 6dcbfeb0a5ea
Revises: 690b6b1f1213
Create Date: 2025-06-16 11:25:06.507780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6dcbfeb0a5ea'
down_revision: Union[str, None] = '690b6b1f1213'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add chat configuration tables."""
    # Create knowledge_sources table
    op.create_table(
        'knowledge_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=False, default='file'),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('s3_bucket', sa.String(255), nullable=True),
        sa.Column('s3_key', sa.String(500), nullable=True),
        sa.Column('s3_url', sa.String(1000), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('processing_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('access_level', sa.String(50), nullable=False, default='private'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.Index('idx_knowledge_sources_account_id', 'account_id'),
        sa.Index('idx_knowledge_sources_type', 'source_type'),
        sa.Index('idx_knowledge_sources_status', 'processing_status'),
        sa.Index('idx_knowledge_sources_created_by', 'created_by'),
    )

    # Create chat_strategies table
    op.create_table(
        'chat_strategies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.Index('idx_chat_strategies_account_id', 'account_id'),
        sa.Index('idx_chat_strategies_created_by', 'created_by'),
    )

    # Create strategy_knowledge_sources junction table
    op.create_table(
        'strategy_knowledge_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, default=1.0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_source_id'], ['knowledge_sources.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('strategy_id', 'knowledge_source_id'),
        sa.Index('idx_strategy_knowledge_strategy_id', 'strategy_id'),
        sa.Index('idx_strategy_knowledge_source_id', 'knowledge_source_id'),
    )

    # Create targeting_rules table
    op.create_table(
        'targeting_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('condition_type', sa.String(50), nullable=False),
        sa.Column('condition_config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.Index('idx_targeting_rules_strategy_id', 'strategy_id'),
    )

    # Create outcome_actions table
    op.create_table(
        'outcome_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_config', sa.JSON(), nullable=False),
        sa.Column('trigger_condition', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.Index('idx_outcome_actions_strategy_id', 'strategy_id'),
    )

    # Create strategy_executions table
    op.create_table(
        'strategy_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('execution_context', sa.JSON(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='SET NULL'),
        sa.Index('idx_strategy_executions_strategy_id', 'strategy_id'),
        sa.Index('idx_strategy_executions_user_id', 'user_id'),
        sa.Index('idx_strategy_executions_session_id', 'session_id'),
        sa.Index('idx_strategy_executions_status', 'status'),
    )

    # Create strategy_analytics table
    op.create_table(
        'strategy_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('dimension_filters', sa.JSON(), nullable=True),
        sa.Column('time_period', sa.String(20), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.Index('idx_strategy_analytics_strategy_id', 'strategy_id'),
        sa.Index('idx_strategy_analytics_metric', 'metric_name'),
        sa.Index('idx_strategy_analytics_time', 'time_period', 'recorded_at'),
    )


def downgrade() -> None:
    """Downgrade schema - Remove chat configuration tables."""
    op.drop_table('strategy_analytics')
    op.drop_table('strategy_executions')
    op.drop_table('outcome_actions')
    op.drop_table('targeting_rules')
    op.drop_table('strategy_knowledge_sources')
    op.drop_table('chat_strategies')
    op.drop_table('knowledge_sources')
