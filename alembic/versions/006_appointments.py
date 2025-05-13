"""Add appointment scheduling tables

Revision ID: 006_appointments
Revises: 005_lab_integration
Create Date: 2025-05-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_appointments'
down_revision = '005_lab_integration'
branch_labels = None
depends_on = None


def upgrade():
    # Create clinician_availability table
    op.create_table(
        'clinician_availability',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('clinician_id', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time_slot', sa.String(5), nullable=False),  # e.g., "10:00"
        sa.Column('available', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_clinician_availability_date', 'clinician_id', 'date'),
    )
    
    # Create appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.String(36), nullable=False),  # UUID
        sa.Column('patient_id', sa.String(36), nullable=False),
        sa.Column('clinician_id', sa.String(36), nullable=False),
        sa.Column('date_time', sa.DateTime(), nullable=False),
        sa.Column('appointment_type', sa.Enum('virtual', 'in-person'), nullable=False),
        sa.Column('status', sa.Enum('scheduled', 'completed', 'canceled', 'rescheduled'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('confirmation_code', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinician_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_appointments_patient', 'patient_id'),
        sa.Index('idx_appointments_clinician', 'clinician_id'),
        sa.Index('idx_appointments_date', 'date_time'),
    )


def downgrade():
    op.drop_table('appointments')
    op.drop_table('clinician_availability')
