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
    # op.add_column('recurring_availability', sa.Column('end_date', sa.Date(), nullable=True))
    op.execute("UPDATE appointments SET time = TIME(date_time)")
    op.alter_column('appointments', 'time', server_default=None)

def downgrade():
    # op.drop_column('recurring_availability', 'end_date')
    pass
