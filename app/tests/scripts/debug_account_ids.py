#!/usr/bin/env python
"""
Debug script to check account ID mismatch issue.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.services.patients import PatientService
    from app.repositories.users import UserRepository
    from app.models.user import User
    from app.models.patient import Patient
    
    print("✓ All imports successful")
    
    # Get a database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("\n=== Debugging Account ID Mismatch ===")
        
        # Find admin@test.com user
        user_repo = UserRepository(db)
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        
        if admin_user:
            print(f"✓ Found admin user:")
            print(f"  - ID: {admin_user.id}")
            print(f"  - Email: {admin_user.email}")
            print(f"  - Role: {admin_user.role}")
            print(f"  - Account ID: {admin_user.account_id}")
        else:
            print("✗ admin@test.com user not found")
            sys.exit(1)
            
        # Get a patient to check its account_id
        patient = db.query(Patient).first()
        if patient:
            print(f"\n✓ Found patient:")
            print(f"  - ID: {patient.id}")
            print(f"  - Name: {patient.first_name} {patient.last_name}")
            print(f"  - Account ID: {patient.account_id}")
            print(f"  - Clinician ID: {patient.clinician_id}")
            
            # Check if account IDs match
            if str(admin_user.account_id) == str(patient.account_id):
                print("✓ Account IDs MATCH - this shouldn't cause authorization issues")
            else:
                print("✗ Account IDs DO NOT MATCH - this is causing the authorization error")
                print(f"  Admin account_id: {admin_user.account_id} (type: {type(admin_user.account_id)})")
                print(f"  Patient account_id: {patient.account_id} (type: {type(patient.account_id)})")
                
            # Test the patient service call
            patient_service = PatientService(db)
            patient_data = patient_service.get_patient_with_invite_status(str(patient.id))
            print(f"\n✓ Patient data from service:")
            print(f"  - Account ID from service: {patient_data.get('account_id')}")
            print(f"  - Type: {type(patient_data.get('account_id'))}")
            
        else:
            print("✗ No patients found")
            
    finally:
        db.close()
        
    print("\n=== SOLUTION ===")
    print("To fix this issue, either:")
    print("1. Make the admin user a SUPER_ADMIN (can update any patient)")
    print("2. Update the patient's account_id to match the admin's account_id")
    print("3. Update the admin's account_id to match the patient's account_id")
    
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
