"""
Add time to appointments and end_date to recurring_availability for compatibility with service/tests
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_add_time_and_end_date'
down_revision = '010_add_date_to_appointments'
branch_labels = None
depends_on = None

def upgrade():
    # Add the time column first
    op.add_column('appointments', sa.Column('time', sa.Time(), nullable=True))
    
    # Add end_date column to recurring_availability if needed
    # op.add_column('recurring_availability', sa.Column('end_date', sa.Date(), nullable=True))
    
    # Check if date_time column exists before trying to update
    from sqlalchemy import inspect
    connection = op.get_bind()
    inspector = inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('appointments')]
    
    if 'date_time' in columns:
        # Use PostgreSQL-compatible syntax to extract time from datetime
        op.execute("UPDATE appointments SET time = date_time::time WHERE date_time IS NOT NULL")
    
    # Remove server default if any
    op.alter_column('appointments', 'time', server_default=None)

def downgrade():
    # op.drop_column('recurring_availability', 'end_date')
    pass
