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
    # Get connection and inspector
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if accounts table exists first, create if it doesn't
    if 'accounts' not in inspector.get_table_names():
        print("✅ Creating accounts table")
        op.create_table(
            'accounts',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('domain', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        print("⚠️  Accounts table already exists, skipping creation")
    
    # Check if chat_strategies table exists
    if 'chat_strategies' not in inspector.get_table_names():
        print("✅ Creating chat_strategies table")
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
    else:
        print("⚠️  Chat strategies table already exists, skipping creation")

    # Check if knowledge_sources table exists
    if 'knowledge_sources' not in inspector.get_table_names():
        print("✅ Creating knowledge_sources table")
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
    else:
        print("⚠️  Knowledge sources table already exists, skipping creation")

    # Check if strategy_knowledge_sources table exists
    if 'strategy_knowledge_sources' not in inspector.get_table_names():
        print("✅ Creating strategy_knowledge_sources table")
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
    else:
        print("⚠️  Strategy knowledge sources table already exists, skipping creation")

    # Check if targeting_rules table exists
    if 'targeting_rules' not in inspector.get_table_names():
        print("✅ Creating targeting_rules table")
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
    else:
        print("⚠️  Targeting rules table already exists, skipping creation")

    # Check if outcome_actions table exists
    if 'outcome_actions' not in inspector.get_table_names():
        print("✅ Creating outcome_actions table")
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
    else:
        print("⚠️  Outcome actions table already exists, skipping creation")

    # Check if strategy_executions table exists
    if 'strategy_executions' not in inspector.get_table_names():
        print("✅ Creating strategy_executions table")
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
            sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        print("⚠️  Strategy executions table already exists, skipping creation")

    # Check if strategy_analytics table exists
    if 'strategy_analytics' not in inspector.get_table_names():
        print("✅ Creating strategy_analytics table")
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
    else:
        print("⚠️  Strategy analytics table already exists, skipping creation")

    # Create indexes for performance - only if tables exist
    existing_tables = inspector.get_table_names()
    
    if 'chat_strategies' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('chat_strategies')]
        
        if 'idx_chat_strategies_account_id' not in existing_indexes:
            op.create_index('idx_chat_strategies_account_id', 'chat_strategies', ['account_id'])
            print("✅ Created index: idx_chat_strategies_account_id")
        else:
            print("⚠️  Index idx_chat_strategies_account_id already exists")
            
        if 'idx_chat_strategies_is_active' not in existing_indexes:
            op.create_index('idx_chat_strategies_is_active', 'chat_strategies', ['is_active'])
            print("✅ Created index: idx_chat_strategies_is_active")
        else:
            print("⚠️  Index idx_chat_strategies_is_active already exists")
            
    if 'knowledge_sources' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('knowledge_sources')]
        
        if 'idx_knowledge_sources_account_id' not in existing_indexes:
            op.create_index('idx_knowledge_sources_account_id', 'knowledge_sources', ['account_id'])
            print("✅ Created index: idx_knowledge_sources_account_id")
        else:
            print("⚠️  Index idx_knowledge_sources_account_id already exists")
            
        if 'idx_knowledge_sources_type' not in existing_indexes:
            op.create_index('idx_knowledge_sources_type', 'knowledge_sources', ['type'])
            print("✅ Created index: idx_knowledge_sources_type")
        else:
            print("⚠️  Index idx_knowledge_sources_type already exists")
            
    if 'targeting_rules' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('targeting_rules')]
        
        if 'idx_targeting_rules_strategy_id' not in existing_indexes:
            op.create_index('idx_targeting_rules_strategy_id', 'targeting_rules', ['strategy_id'])
            print("✅ Created index: idx_targeting_rules_strategy_id")
        else:
            print("⚠️  Index idx_targeting_rules_strategy_id already exists")
            
    if 'outcome_actions' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('outcome_actions')]
        
        if 'idx_outcome_actions_strategy_id' not in existing_indexes:
            op.create_index('idx_outcome_actions_strategy_id', 'outcome_actions', ['strategy_id'])
            print("✅ Created index: idx_outcome_actions_strategy_id")
        else:
            print("⚠️  Index idx_outcome_actions_strategy_id already exists")
            
    if 'strategy_executions' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('strategy_executions')]
        
        if 'idx_strategy_executions_strategy_id' not in existing_indexes:
            op.create_index('idx_strategy_executions_strategy_id', 'strategy_executions', ['strategy_id'])
            print("✅ Created index: idx_strategy_executions_strategy_id")
        else:
            print("⚠️  Index idx_strategy_executions_strategy_id already exists")
            
        if 'idx_strategy_executions_patient_id' not in existing_indexes:
            op.create_index('idx_strategy_executions_patient_id', 'strategy_executions', ['patient_id'])
            print("✅ Created index: idx_strategy_executions_patient_id")
        else:
            print("⚠️  Index idx_strategy_executions_patient_id already exists")
            
    if 'strategy_analytics' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('strategy_analytics')]
        
        if 'idx_strategy_analytics_strategy_id' not in existing_indexes:
            op.create_index('idx_strategy_analytics_strategy_id', 'strategy_analytics', ['strategy_id'])
            print("✅ Created index: idx_strategy_analytics_strategy_id")
        else:
            print("⚠️  Index idx_strategy_analytics_strategy_id already exists")
            
        if 'idx_strategy_analytics_date' not in existing_indexes:
            op.create_index('idx_strategy_analytics_date', 'strategy_analytics', ['date'])
            print("✅ Created index: idx_strategy_analytics_date")
        else:
            print("⚠️  Index idx_strategy_analytics_date already exists")
    else:
        print("⚠️  Strategy analytics table does not exist, skipping index creation")


def downgrade():
    # Drop indexes - only if they exist
    try:
        op.drop_index('idx_strategy_analytics_date', table_name='strategy_analytics')
    except:
        pass
    try:
        op.drop_index('idx_strategy_analytics_strategy_id', table_name='strategy_analytics')
    except:
        pass
    try:
        op.drop_index('idx_strategy_executions_patient_id', table_name='strategy_executions')
    except:
        pass
    try:
        op.drop_index('idx_strategy_executions_strategy_id', table_name='strategy_executions')
    except:
        pass
    try:
        op.drop_index('idx_outcome_actions_strategy_id', table_name='outcome_actions')
    except:
        pass
    try:
        op.drop_index('idx_targeting_rules_strategy_id', table_name='targeting_rules')
    except:
        pass
    try:
        op.drop_index('idx_knowledge_sources_type', table_name='knowledge_sources')
    except:
        pass
    try:
        op.drop_index('idx_knowledge_sources_account_id', table_name='knowledge_sources')
    except:
        pass
    try:
        op.drop_index('idx_chat_strategies_is_active', table_name='chat_strategies')
    except:
        pass
    try:
        op.drop_index('idx_chat_strategies_account_id', table_name='chat_strategies')
    except:
        pass

    # Drop new tables
    try:
        op.drop_table('strategy_analytics')
    except:
        pass
    try:
        op.drop_table('strategy_executions')
    except:
        pass
    try:
        op.drop_table('outcome_actions')
    except:
        pass
    try:
        op.drop_table('targeting_rules')
    except:
        pass
    try:
        op.drop_table('strategy_knowledge_sources')
    except:
        pass
    try:
        op.drop_table('knowledge_sources')
    except:
        pass
    try:
        op.drop_table('chat_strategies')
    except:
        pass
    try:
        op.drop_table('accounts')
    except:
        pass
