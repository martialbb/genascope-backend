#!/usr/bin/env python
"""
Test script to debug the exact authorization logic failing in the patient update endpoint.
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
    from app.models.user import User, UserRole
    from app.models.patient import Patient
    
    print("✓ All imports successful")
    
    # Get a database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("\n=== Testing Authorization Logic ===")
        
        # Get the admin user
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        if not admin_user:
            print("✗ admin@test.com user not found")
            sys.exit(1)
            
        # Get a patient
        patient = db.query(Patient).first()
        if not patient:
            print("✗ No patients found")
            sys.exit(1)
            
        print(f"✓ Admin user found:")
        print(f"  - Role: {admin_user.role}")
        print(f"  - Account ID: {admin_user.account_id} (type: {type(admin_user.account_id)})")
        
        # Get patient data using the service
        patient_service = PatientService(db)
        existing_patient = patient_service.get_patient_with_invite_status(str(patient.id))
        
        print(f"\n✓ Patient data:")
        print(f"  - Account ID: {existing_patient.get('account_id')} (type: {type(existing_patient.get('account_id'))})")
        
        # Test the exact authorization logic from the endpoint
        print(f"\n=== Authorization Logic Test ===")
        
        # Check: current_user.role not in [UserRole.SUPER_ADMIN]
        role_check = admin_user.role not in [UserRole.SUPER_ADMIN]
        print(f"Role check (not SUPER_ADMIN): {role_check}")
        print(f"  Admin role: {admin_user.role}")
        print(f"  SUPER_ADMIN enum: {UserRole.SUPER_ADMIN}")
        
        # Check: current_user.account_id exists
        account_id_exists = bool(admin_user.account_id)
        print(f"Account ID exists: {account_id_exists}")
        
        # Check: account IDs don't match
        account_ids_dont_match = existing_patient.get("account_id") != admin_user.account_id
        print(f"Account IDs don't match: {account_ids_dont_match}")
        print(f"  Patient account_id: '{existing_patient.get('account_id')}'")
        print(f"  Admin account_id: '{admin_user.account_id}'")
        print(f"  String comparison: '{existing_patient.get('account_id')}' != '{admin_user.account_id}' = {existing_patient.get('account_id') != admin_user.account_id}")
        
        # Full authorization check
        authorization_fails = (role_check and account_id_exists and account_ids_dont_match)
        print(f"\nFull authorization check fails: {authorization_fails}")
        
        if authorization_fails:
            print("❌ AUTHORIZATION WOULD FAIL")
        else:
            print("✅ AUTHORIZATION WOULD PASS")
            
    finally:
        db.close()
        
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
