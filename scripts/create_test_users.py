#!/usr/bin/env python3
"""
Create test users in the database for manual testing.

This script creates the following test users:
1. Super Admin - Full system access
2. Admin - Organization admin access
3. Clinician - Patient management and clinical features
4. Lab Tech - Lab test management
5. Patient - Patient portal access

Usage:
    python create_test_users.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import get_db, engine
from app.models.user import User, Account, UserRole
from app.services.users import UserService
import uuid
from datetime import datetime

def create_test_account(db: Session) -> Account:
    """Create a test account for the test users"""
    account_data = {
        "id": "test-account-001",
        "name": "Test Hospital System",
        "domain": "testhospital.com",
        "is_active": True
    }
    
    # Check if account already exists
    existing_account = db.query(Account).filter(Account.id == account_data["id"]).first()
    if existing_account:
        print(f"✅ Test account already exists: {existing_account.name}")
        return existing_account
    
    account = Account(**account_data)
    db.add(account)
    db.commit()
    db.refresh(account)
    print(f"✅ Created test account: {account.name}")
    return account

def create_test_users(db: Session):
    """Create test users for manual testing"""
    user_service = UserService(db)
    account = create_test_account(db)
    
    # Test users to create
    test_users = [
        {
            "id": "super-admin-001",
            "email": "superadmin@genascope.com",
            "name": "Super Admin User",
            "role": UserRole.SUPER_ADMIN,
            "password": "SuperAdmin123!",
            "account_id": None,  # Super admin not tied to specific account
            "description": "System super administrator with full access"
        },
        {
            "id": "admin-001", 
            "email": "admin@testhospital.com",
            "name": "Admin User",
            "role": UserRole.ADMIN,
            "password": "Admin123!",
            "account_id": account.id,
            "description": "Organization administrator"
        },
        {
            "id": "admin-test-001", 
            "email": "admin@test.com",
            "name": "Test Admin",
            "role": UserRole.ADMIN,
            "password": "test123",
            "account_id": account.id,
            "description": "Simple test admin for quick development login"
        },
        {
            "id": "clinician-001",
            "email": "clinician@testhospital.com", 
            "name": "Dr. Jane Smith",
            "role": UserRole.CLINICIAN,
            "password": "Clinician123!",
            "account_id": account.id,
            "description": "Genetic counselor and clinician"
        },
        {
            "id": "clinician-002",
            "email": "clinician2@testhospital.com",
            "name": "Dr. John Davis", 
            "role": UserRole.CLINICIAN,
            "password": "Clinician123!",
            "account_id": account.id,
            "description": "Oncologist and clinician"
        },
        {
            "id": "labtech-001",
            "email": "labtech@testhospital.com",
            "name": "Lab Tech User",
            "role": UserRole.LAB_TECH,
            "password": "LabTech123!",
            "account_id": account.id,
            "description": "Laboratory technician"
        },
        {
            "id": "patient-001",
            "email": "patient1@example.com",
            "name": "John Doe",
            "role": UserRole.PATIENT,
            "password": "Patient123!",
            "account_id": account.id,
            "clinician_id": "clinician-001",
            "description": "Test patient for risk assessment"
        },
        {
            "id": "patient-002", 
            "email": "patient2@example.com",
            "name": "Jane Johnson",
            "role": UserRole.PATIENT,
            "password": "Patient123!",
            "account_id": account.id,
            "clinician_id": "clinician-001",
            "description": "Test patient for appointments"
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        description = user_data.pop("description")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"⚠️  User already exists: {user_data['email']} ({existing_user.role})")
            created_users.append(existing_user)
            continue
        
        try:
            # Create user
            user = user_service.create_user(user_data)
            created_users.append(user)
            print(f"✅ Created {user.role} user: {user.email} - {user.name}")
            print(f"   Password: {user_data['password']}")
            print(f"   Description: {description}")
            print()
        except Exception as e:
            print(f"❌ Failed to create user {user_data['email']}: {str(e)}")
    
    return created_users

def print_test_credentials(users):
    """Print test user credentials for easy reference"""
    print("\n" + "="*80)
    print("TEST USER CREDENTIALS FOR MANUAL TESTING")
    print("="*80)
    
    role_groups = {
        UserRole.SUPER_ADMIN: [],
        UserRole.ADMIN: [],
        UserRole.CLINICIAN: [], 
        UserRole.LAB_TECH: [],
        UserRole.PATIENT: []
    }
    
    for user in users:
        role_groups[user.role].append(user)
    
    for role, users_in_role in role_groups.items():
        if users_in_role:
            print(f"\n🔐 {role.upper()} USERS:")
            print("-" * 40)
            for user in users_in_role:
                # Get password from the test users data
                test_passwords = {
                    "superadmin@genascope.com": "SuperAdmin123!",
                    "admin@testhospital.com": "Admin123!",
                    "clinician@testhospital.com": "Clinician123!",
                    "clinician2@testhospital.com": "Clinician123!",
                    "labtech@testhospital.com": "LabTech123!",
                    "patient1@example.com": "Patient123!",
                    "patient2@example.com": "Patient123!"
                }
                password = test_passwords.get(user.email, "Unknown")
                
                print(f"📧 Email: {user.email}")
                print(f"👤 Name: {user.name}")
                print(f"🔑 Password: {password}")
                print(f"🆔 ID: {user.id}")
                if hasattr(user, 'account_id') and user.account_id:
                    print(f"🏥 Account: {user.account_id}")
                print()

def main():
    """Main function to create test users"""
    print("🚀 Creating test users for Genascope application...\n")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Create test users
        users = create_test_users(db)
        
        # Print credentials
        print_test_credentials(users)
        
        print("✅ Test user creation completed successfully!")
        print("\n💡 Use these credentials to test different user roles and features.")
        print("💡 All passwords follow the pattern: [Role]123! (e.g., Admin123!)")
        
    except Exception as e:
        print(f"❌ Error creating test users: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
