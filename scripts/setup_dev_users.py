#!/usr/bin/env python3
"""
Development User Setup Script
Creates test users for immediate development and testing
"""

import os
import sys
import asyncio
import logging

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.core.database import get_db_session
from app.services.user_service import UserService
from app.models.user import User, UserRole
from app.models.account import Account
from app.models.patient_profile import PatientProfile
from sqlalchemy.ext.asyncio import AsyncSession

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_dev_users():
    """Create test users for development including the specific admin@test.com user"""
    
    logger.info("🚀 Starting development user creation...")
    
    async for session in get_db_session():
        try:
            # Initialize services
            user_service = UserService(session)
            
            # Create test account
            account = Account(
                id="test-hospital-001",
                name="Test Hospital",
                domain="testhospital.com",
                subscription_tier="premium",
                is_active=True
            )
            session.add(account)
            await session.commit()
            await session.refresh(account)
            logger.info(f"✅ Created test account: {account.name}")
            
            # Define test users - including the specific admin@test.com requested
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
                    "id": "admin-test-quick", 
                    "email": "admin@test.com",
                    "name": "Quick Test Admin",
                    "role": UserRole.ADMIN,
                    "password": "test123",
                    "account_id": account.id,
                    "description": "Simple admin for quick login during development"
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
            
            # Create users
            created_users = []
            clinician_ids = {}
            
            for user_data in test_users:
                try:
                    # Check if user already exists
                    existing_user = await user_service.get_user_by_email(user_data["email"])
                    if existing_user:
                        logger.info(f"⚠️  User {user_data['email']} already exists, skipping...")
                        if user_data["role"] == UserRole.CLINICIAN:
                            clinician_ids[user_data["id"]] = existing_user.id
                        continue
                    
                    # Create user
                    user = await user_service.create_user(
                        id=user_data["id"],
                        email=user_data["email"],
                        name=user_data["name"],
                        password=user_data["password"],
                        role=user_data["role"],
                        account_id=user_data["account_id"]
                    )
                    
                    created_users.append(user)
                    
                    # Store clinician IDs for patient assignment
                    if user_data["role"] == UserRole.CLINICIAN:
                        clinician_ids[user_data["id"]] = user.id
                    
                    logger.info(f"✅ Created {user_data['role'].value}: {user_data['email']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create user {user_data['email']}: {str(e)}")
                    continue
            
            # Create patient profiles for patient users
            for user_data in test_users:
                if user_data["role"] == UserRole.PATIENT and "clinician_id" in user_data:
                    try:
                        # Find the created patient user
                        patient_user = next((u for u in created_users if u.email == user_data["email"]), None)
                        if not patient_user:
                            continue
                        
                        # Get clinician ID
                        clinician_db_id = clinician_ids.get(user_data["clinician_id"])
                        if not clinician_db_id:
                            logger.warning(f"⚠️  Clinician {user_data['clinician_id']} not found for patient {user_data['email']}")
                            continue
                        
                        # Create patient profile
                        patient_profile = PatientProfile(
                            user_id=patient_user.id,
                            clinician_id=clinician_db_id,
                            date_of_birth=None,  # Will be set later
                            medical_record_number=f"MRN-{user_data['id'][-3:]}",
                            emergency_contact_name="Emergency Contact",
                            emergency_contact_phone="555-0123"
                        )
                        
                        session.add(patient_profile)
                        logger.info(f"✅ Created patient profile for {user_data['email']}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to create patient profile for {user_data['email']}: {str(e)}")
                        continue
            
            await session.commit()
            
            logger.info("🎉 Development user creation completed!")
            logger.info("\n" + "="*60)
            logger.info("📝 QUICK LOGIN CREDENTIALS:")
            logger.info("   Email: admin@test.com")
            logger.info("   Password: test123")
            logger.info("   Role: Admin")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create development users: {str(e)}")
            await session.rollback()
            return False
        finally:
            await session.close()

if __name__ == "__main__":
    try:
        success = asyncio.run(create_dev_users())
        if success:
            logger.info("✅ Development user setup completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Development user setup failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error in development user setup: {str(e)}")
        sys.exit(1)
