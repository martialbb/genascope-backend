"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-05-01 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Example: Create users and patients tables (minimal for chain)
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'patients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create a trigger function for updating timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION update_modified_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for automatic timestamp updates
    op.execute("""
        CREATE TRIGGER update_users_modtime
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_patients_modtime
        BEFORE UPDATE ON patients
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    """)

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS update_patients_modtime ON patients")
    op.execute("DROP TRIGGER IF EXISTS update_users_modtime ON users")
    op.execute("DROP FUNCTION IF EXISTS update_modified_column()")
    op.drop_table('patients')
    op.drop_table('users')
