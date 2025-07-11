#!/usr/bin/env python3
"""
Simple script to create test users with localhost database connection.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Override database URL to use localhost
DATABASE_URL = "postgresql://genascope:genascope@localhost:5432/genascope"

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.user import User, UserRole
from app.models.accounts import Account
from app.db.database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_users():
    """Create test users for API testing."""
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create test account
        account_data = {
            "id": "test-account-1",
            "name": "Test Healthcare Organization",
            "status": "active"
        }
        
        existing_account = db.query(Account).filter(Account.id == account_data["id"]).first()
        if not existing_account:
            account = Account(**account_data)
            db.add(account)
            print(f"✅ Created account: {account.name}")
        else:
            account = existing_account
            print(f"ℹ️ Account already exists: {account.name}")
        
        # Create admin user
        admin_data = {
            "id": "admin-user-1",
            "email": "admin@test.com",
            "password": pwd_context.hash("test123"),
            "first_name": "Admin",
            "last_name": "User",
            "role": UserRole.ADMIN,
            "account_id": account.id,
            "is_active": True,
            "is_verified": True
        }
        
        existing_admin = db.query(User).filter(User.email == admin_data["email"]).first()
        if not existing_admin:
            admin = User(**admin_data)
            db.add(admin)
            print(f"✅ Created admin user: {admin.email}")
        else:
            print(f"ℹ️ Admin user already exists: {existing_admin.email}")
        
        # Create clinician user
        clinician_data = {
            "id": "clinician-user-1",
            "email": "clinician@test.com", 
            "password": pwd_context.hash("test123"),
            "first_name": "Test",
            "last_name": "Clinician",
            "role": UserRole.CLINICIAN,
            "account_id": account.id,
            "is_active": True,
            "is_verified": True
        }
        
        existing_clinician = db.query(User).filter(User.email == clinician_data["email"]).first()
        if not existing_clinician:
            clinician = User(**clinician_data)
            db.add(clinician)
            print(f"✅ Created clinician user: {clinician.email}")
        else:
            print(f"ℹ️ Clinician user already exists: {existing_clinician.email}")
        
        db.commit()
        print("\n🚀 Test users created successfully!")
        print(f"Admin: admin@test.com / test123")
        print(f"Clinician: clinician@test.com / test123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test users: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating test users for Patient API testing...")
    create_test_users()
