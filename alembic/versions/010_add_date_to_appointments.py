"""
Add date column to appointments table for compatibility with repository/service/tests
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_add_date_to_appointments'
down_revision = ('e3584a1531df', '72b453920928')
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('appointments', sa.Column('date', sa.Date(), nullable=False, server_default=sa.text("'1970-01-01'")))
    op.execute("UPDATE appointments SET date = DATE(date_time)")
    op.alter_column('appointments', 'date', server_default=None)

def downgrade():
    op.drop_column('appointments', 'date')
