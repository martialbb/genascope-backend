"""Add missing chat configuration tables

Revision ID: 014_chat_config_complete
Revises: 663cd5e819c6
Create Date: 2025-07-04 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '014_chat_config_complete'
down_revision: Union[str, None] = '663cd5e819c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing chat configuration tables."""
    
    # Create targeting_rules table
    op.create_table('targeting_rules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('field', sa.String(), nullable=False),
        sa.Column('operator', sa.String(), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create outcome_actions table
    op.create_table('outcome_actions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create strategy_executions table
    op.create_table('strategy_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('triggered_by', sa.String(), nullable=True),
        sa.Column('trigger_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_status', sa.String(), nullable=False),
        sa.Column('outcome_result', sa.String(), nullable=True),
        sa.Column('executed_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id']),
        sa.ForeignKeyConstraint(['session_id'], ['ai_chat_sessions.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id']),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create strategy_analytics table
    op.create_table('strategy_analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('patients_screened', sa.Integer(), nullable=False),
        sa.Column('criteria_met', sa.Integer(), nullable=False),
        sa.Column('criteria_not_met', sa.Integer(), nullable=False),
        sa.Column('incomplete_data', sa.Integer(), nullable=False),
        sa.Column('avg_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('tasks_created', sa.Integer(), nullable=False),
        sa.Column('charts_flagged', sa.Integer(), nullable=False),
        sa.Column('messages_sent', sa.Integer(), nullable=False),
        sa.Column('followups_scheduled', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_id', 'date')
    )

    # Create strategy_knowledge_sources table
    op.create_table('strategy_knowledge_sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('knowledge_source_id', sa.String(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['chat_strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_source_id'], ['knowledge_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_id', 'knowledge_source_id')
    )

    # Set default values
    op.execute("ALTER TABLE targeting_rules ALTER COLUMN sequence SET DEFAULT 0")
    op.execute("ALTER TABLE targeting_rules ALTER COLUMN is_active SET DEFAULT true")
    
    op.execute("ALTER TABLE outcome_actions ALTER COLUMN sequence SET DEFAULT 0")
    op.execute("ALTER TABLE outcome_actions ALTER COLUMN is_active SET DEFAULT true")
    
    op.execute("ALTER TABLE strategy_executions ALTER COLUMN execution_status SET DEFAULT 'in_progress'")
    
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN patients_screened SET DEFAULT 0")
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN criteria_met SET DEFAULT 0")
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN criteria_not_met SET DEFAULT 0")
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN incomplete_data SET DEFAULT 0")
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN tasks_created SET DEFAULT 0")
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN charts_flagged SET DEFAULT 0")
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN messages_sent SET DEFAULT 0")
    op.execute("ALTER TABLE strategy_analytics ALTER COLUMN followups_scheduled SET DEFAULT 0")
    
    op.execute("ALTER TABLE strategy_knowledge_sources ALTER COLUMN weight SET DEFAULT 1.0")
    op.execute("ALTER TABLE strategy_knowledge_sources ALTER COLUMN is_active SET DEFAULT true")


def downgrade() -> None:
    """Remove chat configuration tables."""
    op.drop_table('strategy_knowledge_sources')
    op.drop_table('strategy_analytics')
    op.drop_table('strategy_executions')
    op.drop_table('outcome_actions')
    op.drop_table('targeting_rules')
