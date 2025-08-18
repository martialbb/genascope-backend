#!/usr/bin/env python3
"""
Create essential admin user for production deployment.
This script creates a minimal admin user for authentication testing.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.services.users import UserService
from app.schemas.users import UserRole

def create_admin_user():
    """Create the basic admin user for authentication."""
    session = SessionLocal()
    try:
        user_service = UserService(session)
        
        # Check if admin user already exists
        existing_user = user_service.user_repository.get_by_email('admin@test.com')
        if existing_user:
            print(f"✅ Admin user already exists: {existing_user.email}")
            return True
        
        # Create admin user
        user_data = {
            'email': 'admin@test.com',
            'password': 'test123',
            'name': 'Admin User',
            'role': UserRole.ADMIN,
            'is_active': True
        }
        
        user = user_service.create_user(user_data)
        print(f"✅ Created admin user: {user.email} with ID: {user.id}")
        print(f"🔑 Login credentials: admin@test.com / test123")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("🔧 Creating essential admin user...")
    success = create_admin_user()
    sys.exit(0 if success else 1)
