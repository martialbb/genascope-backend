#!/usr/bin/env python
"""
Test script to verify the authorization fix is working correctly.
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
        print("\n=== Testing Authorization Fix ===")
        
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
            
        # Get patient data using the service
        patient_service = PatientService(db)
        existing_patient = patient_service.get_patient_with_invite_status(str(patient.id))
        
        print(f"✓ Testing with:")
        print(f"  - Admin account_id: {admin_user.account_id} (type: {type(admin_user.account_id)})")
        print(f"  - Patient account_id: {existing_patient.get('account_id')} (type: {type(existing_patient.get('account_id'))})")
        
        # Test the FIXED authorization logic
        print(f"\n=== Fixed Authorization Logic Test ===")
        
        # Check: current_user.role not in [UserRole.SUPER_ADMIN]
        role_check = admin_user.role not in [UserRole.SUPER_ADMIN]
        print(f"Role check (not SUPER_ADMIN): {role_check}")
        
        # Check: current_user.account_id exists
        account_id_exists = bool(admin_user.account_id)
        print(f"Account ID exists: {account_id_exists}")
        
        # Check: account IDs don't match (FIXED with str() conversion)
        account_ids_dont_match = str(existing_patient.get("account_id")) != str(admin_user.account_id)
        print(f"Account IDs don't match (with str() conversion): {account_ids_dont_match}")
        print(f"  str(Patient account_id): '{str(existing_patient.get('account_id'))}'")
        print(f"  str(Admin account_id): '{str(admin_user.account_id)}'")
        print(f"  String comparison: '{str(existing_patient.get('account_id'))}' != '{str(admin_user.account_id)}' = {str(existing_patient.get('account_id')) != str(admin_user.account_id)}")
        
        # Full authorization check with fix
        authorization_fails = (role_check and account_id_exists and account_ids_dont_match)
        print(f"\nFull authorization check fails: {authorization_fails}")
        
        if authorization_fails:
            print("❌ AUTHORIZATION WOULD STILL FAIL")
        else:
            print("✅ AUTHORIZATION WOULD NOW PASS!")
            
        print(f"\n=== Summary ===")
        if not authorization_fails:
            print("✅ AUTHORIZATION FIX SUCCESSFUL!")
            print("✅ admin@test.com should now be able to update patients")
            print("✅ The patient update API should work correctly")
        else:
            print("❌ Authorization is still failing - additional investigation needed")
            
    finally:
        db.close()
        
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
