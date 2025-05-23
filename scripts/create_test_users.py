#!/usr/bin/env python3
"""
Script to create test users in the database for manual testing
"""
import sys
import os
import uuid
from datetime import datetime

# Add the app directory to the Python path
sys.path.append('/app')

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.users import UserService
from app.models.user import UserRole

def create_test_users():
    """Create test users for manual testing"""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        
        # Test users to create
        test_users = [
            {
                "id": "test-clinician-1",
                "email": "clinician@test.com",
                "password": "TestPass123!",
                "name": "Dr. Test Clinician",
                "role": UserRole.CLINICIAN,
                "is_active": True
            },
            {
                "id": "test-admin-1", 
                "email": "admin@test.com",
                "password": "AdminPass123!",
                "name": "Test Admin",
                "role": UserRole.ADMIN,
                "is_active": True
            },
            {
                "id": "test-superuser-1",
                "email": "superuser@test.com", 
                "password": "SuperPass123!",
                "name": "Test Superuser",
                "role": UserRole.SUPER_ADMIN,
                "is_active": True
            },
            {
                "id": "test-patient-1",
                "email": "patient@test.com",
                "password": "PatientPass123!",
                "name": "Test Patient",
                "role": UserRole.PATIENT,
                "is_active": True,
                "clinician_id": "test-clinician-1"
            },
            {
                "id": "test-labtech-1",
                "email": "labtech@test.com",
                "password": "LabTechPass123!",
                "name": "Test Lab Technician",
                "role": UserRole.LAB_TECH,
                "is_active": True
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            try:
                # Check if user already exists
                existing_user = user_service.get_user_by_email(user_data["email"])
                if existing_user:
                    print(f"User {user_data['email']} already exists, skipping...")
                    continue
                
                # Create the user
                user = user_service.create_user(user_data.copy())
                created_users.append(user)
                print(f"Created user: {user.email} ({user.role}) - ID: {user.id}")
                
            except Exception as e:
                print(f"Error creating user {user_data['email']}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        print(f"\nSuccessfully created {len(created_users)} test users!")
        print("\nTest User Credentials:")
        print("=====================")
        for user_data in test_users:
            if any(u.email == user_data["email"] for u in created_users):
                print(f"Email: {user_data['email']}")
                print(f"Password: {user_data['password']}")
                print(f"Role: {user_data['role']}")
                print(f"ID: {user_data['id']}")
                print("---")
        
        return True
        
    except Exception as e:
        print(f"Error creating test users: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating test users for manual testing...")
    success = create_test_users()
    if success:
        print("\nTest users created successfully!")
        sys.exit(0)
    else:
        print("\nFailed to create test users!")
        sys.exit(1)
