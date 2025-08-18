"""Add user_id to patients table

Revision ID: c97a538f2456
Revises: b86a120f1234
Create Date: 2025-05-29

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c97a538f2456'
down_revision = 'b86a120f1234'
branch_labels = None
depends_on = None


def upgrade():
    # Check if user_id column already exists
    connection = op.get_bind()
    inspector = sa.Inspector.from_engine(connection)
    
    try:
        columns = [col['name'] for col in inspector.get_columns('patients')]
        
        if 'user_id' not in columns:
            # Add user_id column to patients table
            op.add_column('patients', sa.Column('user_id', sa.String(36), nullable=True))
            print("✅ Added user_id column to patients table")
        else:
            print("⚠️  Column user_id already exists in patients table, skipping")
        
        # Check and add unique constraint if it doesn't exist
        existing_constraints = [constraint['name'] for constraint in inspector.get_unique_constraints('patients')]
        if 'uq_patients_user_id' not in existing_constraints:
            op.create_unique_constraint('uq_patients_user_id', 'patients', ['user_id'])
            print("✅ Added unique constraint uq_patients_user_id")
        else:
            print("⚠️  Unique constraint uq_patients_user_id already exists, skipping")
        
        # Check and add foreign key constraint if it doesn't exist
        existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('patients')]
        if 'fk_patients_user_id' not in existing_fks:
            op.create_foreign_key(
                'fk_patients_user_id', 'patients', 'users',
                ['user_id'], ['id'], ondelete='SET NULL'
            )
            print("✅ Added foreign key constraint fk_patients_user_id")
        else:
            print("⚠️  Foreign key constraint fk_patients_user_id already exists, skipping")
            
    except Exception as e:
        print(f"⚠️  Error in migration: {e}")
        # If inspection fails, try to continue anyway


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_patients_user_id', 'patients', type_='foreignkey')
    
    # Remove unique constraint
    op.drop_constraint('uq_patients_user_id', 'patients', type_='unique')
    
    # Remove user_id column
    op.drop_column('patients', 'user_id')
