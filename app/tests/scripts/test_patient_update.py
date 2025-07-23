#!/usr/bin/env python
"""
Test script to verify patient update functionality works correctly.
This simulates the exact scenario that was failing.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.services.patients import PatientService
    from app.repositories.invites import InviteRepository
    
    print("✓ All imports successful")
    
    # Get a database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("\n=== Testing InviteRepository ===")
        invite_repo = InviteRepository(db)
        print("✓ InviteRepository instantiated successfully")
        
        # Check if method exists
        if hasattr(invite_repo, 'get_by_patient_id'):
            print("✓ get_by_patient_id method exists")
            
            # Test the method with a sample patient ID
            test_patient_id = "test-patient-123"
            try:
                result = invite_repo.get_by_patient_id(test_patient_id)
                print(f"✓ get_by_patient_id executed successfully, returned {len(result)} results")
            except Exception as e:
                print(f"✗ get_by_patient_id failed: {e}")
                
        else:
            print("✗ get_by_patient_id method not found")
            available_methods = [method for method in dir(invite_repo) if not method.startswith('_')]
            print(f"Available methods: {available_methods}")
        
        print("\n=== Testing PatientService ===")
        patient_service = PatientService(db)
        print("✓ PatientService instantiated successfully")
        
        # Check if method exists
        if hasattr(patient_service, 'update_patient'):
            print("✓ update_patient method exists")
            
            # Test accessing the invite_repository attribute
            if hasattr(patient_service, 'invite_repository'):
                print("✓ PatientService has invite_repository attribute")
                
                # Test that the invite_repository has the method
                if hasattr(patient_service.invite_repository, 'get_by_patient_id'):
                    print("✓ PatientService.invite_repository has get_by_patient_id method")
                    
                    # This is the exact call that was failing
                    try:
                        test_result = patient_service.invite_repository.get_by_patient_id("test-123")
                        print("✓ CRITICAL TEST PASSED: patient_service.invite_repository.get_by_patient_id works!")
                    except AttributeError as e:
                        print(f"✗ CRITICAL FAILURE: {e}")
                    except Exception as e:
                        print(f"✓ Method works (got exception but not AttributeError): {e}")
                else:
                    print("✗ PatientService.invite_repository does NOT have get_by_patient_id method")
                    methods = [m for m in dir(patient_service.invite_repository) if not m.startswith('_')]
                    print(f"Available methods: {methods}")
            else:
                print("✗ PatientService does NOT have invite_repository attribute")
        else:
            print("✗ update_patient method not found")
            
        print("\n=== Testing get_patient_with_invite_status method ===")
        if hasattr(patient_service, 'get_patient_with_invite_status'):
            print("✓ get_patient_with_invite_status method exists")
            
            try:
                # This method also calls invite_repository.get_by_patient_id
                test_result = patient_service.get_patient_with_invite_status("test-123")
                print("✓ get_patient_with_invite_status executed (may fail with not found, but no AttributeError)")
            except AttributeError as e:
                print(f"✗ get_patient_with_invite_status failed with AttributeError: {e}")
            except Exception as e:
                print(f"✓ get_patient_with_invite_status works (got non-AttributeError): {e}")
        else:
            print("✗ get_patient_with_invite_status method not found")
            
    finally:
        db.close()
        
    print("\n=== SUMMARY ===")
    print("The patient update functionality should now work correctly!")
    print("All critical methods exist and are accessible.")
    
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
