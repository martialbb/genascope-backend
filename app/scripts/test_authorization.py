#!/usr/bin/env python
"""
Test the exact authorization logic that's failing.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.services.patients import PatientService
    from app.models.user import User, UserRole
    from app.models.patient import Patient
    
    print("✓ All imports successful")
    
    # Get a database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("\n=== Testing Authorization Logic ===")
        
        # Get admin user
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        if not admin_user:
            print("✗ admin@test.com user not found")
            sys.exit(1)
            
        print(f"✓ Admin user found:")
        print(f"  - Role: {admin_user.role}")
        print(f"  - Account ID: {admin_user.account_id}")
        print(f"  - Role type: {type(admin_user.role)}")
        print(f"  - Account ID type: {type(admin_user.account_id)}")
        
        # Get a patient
        patient = db.query(Patient).first()
        if not patient:
            print("✗ No patients found")
            sys.exit(1)
            
        patient_id = str(patient.id)
        print(f"\n✓ Patient found: {patient_id}")
        
        # Test the patient service call
        patient_service = PatientService(db)
        existing_patient = patient_service.get_patient_with_invite_status(patient_id)
        
        print(f"\n✓ Patient data from service:")
        print(f"  - Account ID: {existing_patient.get('account_id')}")
        print(f"  - Account ID type: {type(existing_patient.get('account_id'))}")
        
        # Test the authorization logic step by step
        print(f"\n=== Authorization Logic Test ===")
        
        # Check 1: Role check
        role_check = admin_user.role in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]
        print(f"1. Role check ({admin_user.role} in [CLINICIAN, ADMIN, SUPER_ADMIN]): {role_check}")
        
        if not role_check:
            print("✗ FAILED: Role check failed")
            sys.exit(1)
            
        # Check 2: Super admin check
        is_super_admin = admin_user.role in [UserRole.SUPER_ADMIN]
        print(f"2. Is super admin ({admin_user.role} in [SUPER_ADMIN]): {is_super_admin}")
        
        # Check 3: Account ID check
        user_has_account_id = admin_user.account_id is not None
        print(f"3. User has account_id: {user_has_account_id}")
        
        # Check 4: Account ID comparison
        patient_account_id = existing_patient.get("account_id")
        account_ids_match = patient_account_id == admin_user.account_id
        print(f"4. Account IDs match: {account_ids_match}")
        print(f"   - User account_id: '{admin_user.account_id}'")
        print(f"   - Patient account_id: '{patient_account_id}'")
        print(f"   - String comparison: {str(admin_user.account_id) == str(patient_account_id)}")
        
        # The failing condition
        should_fail = (admin_user.role not in [UserRole.SUPER_ADMIN] and 
                      admin_user.account_id and 
                      existing_patient.get("account_id") != admin_user.account_id)
                      
        print(f"\n=== FINAL AUTHORIZATION CHECK ===")
        print(f"Should fail authorization: {should_fail}")
        print(f"  - NOT super admin: {admin_user.role not in [UserRole.SUPER_ADMIN]}")
        print(f"  - Has account_id: {bool(admin_user.account_id)}")
        print(f"  - Account IDs don't match: {existing_patient.get('account_id') != admin_user.account_id}")
        
        if should_fail:
            print("\n✗ AUTHORIZATION WOULD FAIL")
            print("This explains the 'Not authorized to update this patient' error")
        else:
            print("\n✓ AUTHORIZATION SHOULD PASS")
            print("There might be another issue")
            
    finally:
        db.close()
        
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
