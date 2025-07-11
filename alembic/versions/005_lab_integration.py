"""Add lab integration tables

Revision ID: 005_lab_integration
Revises: 004_eligibility_analysis
Create Date: 2025-05-10 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_lab_integration'
down_revision = '004_eligibility_analysis'
branch_labels = None
depends_on = None

def upgrade():
    # Create lab_integrations table
    op.create_table(
        'lab_integrations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('lab_name', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False),
        sa.Column('api_url', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create lab_orders table
    op.create_table(
        'lab_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('patient_id', sa.String(36), nullable=False),
        sa.Column('clinician_id', sa.String(36), nullable=False),
        sa.Column('lab_id', sa.String(36), sa.ForeignKey('lab_integrations.id'), nullable=True),
        sa.Column('external_order_id', sa.String(255), nullable=True),
        sa.Column('order_number', sa.String(32), nullable=False, unique=True),
        sa.Column('test_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('requisition_details', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('collection_date', sa.DateTime(), nullable=True),
        sa.Column('completed_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinician_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_lab_orders_patient', 'patient_id'),
        sa.Index('idx_lab_orders_clinician', 'clinician_id'),
        sa.Index('idx_lab_orders_lab', 'lab_id'),
    )

    # Create lab_results table
    op.create_table(
        'lab_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('lab_orders.id'), nullable=False),
        sa.Column('result_status', sa.String(32), nullable=False),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('report_url', sa.String(255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('abnormal', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('reviewed', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('reviewed_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['order_id'], ['lab_orders.id'], ondelete='CASCADE'),
        sa.Index('idx_lab_results_order', 'order_id'),
        sa.Index('idx_lab_results_reviewer', 'reviewed_by'),
    )

def downgrade():
    op.drop_table('lab_results')
    op.drop_table('lab_orders')
    op.drop_table('lab_integrations')
