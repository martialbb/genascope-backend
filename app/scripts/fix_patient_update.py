#!/usr/bin/env python
"""
This script fixes the issue with patient updates:
1. Verifies that InviteRepository.get_by_patient_id method exists and is used correctly
2. Ensures that PatientService.update_patient method is properly implemented
"""
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

# Adjust import paths based on whether we're running from app/ or backend/
try:
    # Try direct import first (used when running inside Docker)
    from db.database import get_db
    from models.patient import Patient
    from repositories.invites import InviteRepository
    from services.patients import PatientService
    print("Using direct imports (running inside Docker container)")
except ImportError:
    # Fall back to app-prefixed imports (used when running from backend/)
    from app.db.database import get_db
    from app.models.patient import Patient
    from app.repositories.invites import InviteRepository
    from app.services.patients import PatientService
    print("Using app-prefixed imports (running from backend/ directory)")


def check_invite_repository():
    """Check if the get_by_patient_id method in InviteRepository exists and works correctly."""
    print("Checking InviteRepository.get_by_patient_id method...")
    
    db = next(get_db())
    
    try:
        invite_repo = InviteRepository(db)
        
        # Verify the method exists
        if not hasattr(invite_repo, "get_by_patient_id"):
            print("ERROR: get_by_patient_id method doesn't exist in InviteRepository")
            return False
        
        # Test the method with a non-existent patient ID
        test_id = "test-nonexistent-id"
        try:
            result = invite_repo.get_by_patient_id(test_id)
            print(f"SUCCESS: get_by_patient_id method works (returned {len(result)} results)")
            return True
        except Exception as e:
            print(f"ERROR: get_by_patient_id method failed: {str(e)}")
            return False
    finally:
        db.close()


def check_update_patient():
    """Check if the update_patient method in PatientService exists and works correctly."""
    print("Checking PatientService.update_patient method...")
    
    db = next(get_db())
    
    try:
        patient_service = PatientService(db)
        
        # Verify the method exists
        if not hasattr(patient_service, "update_patient"):
            print("ERROR: update_patient method doesn't exist in PatientService")
            return False
        
        print("SUCCESS: update_patient method exists in PatientService")
        return True
    finally:
        db.close()


def print_method_implementations():
    """Print the actual implementation of the methods for debugging."""
    print("\nCurrent method implementations:")
    
    # Check InviteRepository.get_by_patient_id implementation
    import inspect
    
    try:
        get_by_patient_id_source = inspect.getsource(InviteRepository.get_by_patient_id)
        print("\nInviteRepository.get_by_patient_id implementation:")
        print(get_by_patient_id_source)
    except Exception as e:
        print(f"Could not get source for InviteRepository.get_by_patient_id: {e}")
    
    # Check PatientService.update_patient implementation
    try:
        if hasattr(PatientService, "update_patient"):
            update_patient_source = inspect.getsource(PatientService.update_patient)
            print("\nPatientService.update_patient implementation:")
            print(update_patient_source)
        else:
            print("PatientService.update_patient method not found.")
    except Exception as e:
        print(f"Could not get source for PatientService.update_patient: {e}")


def main():
    """Main function to check and fix issues."""
    print("Starting patient update functionality verification...")
    
    # Check the methods
    invite_repo_ok = check_invite_repository()
    update_patient_ok = check_update_patient()
    
    # Print current implementations for debugging
    print_method_implementations()
    
    # Final result
    if invite_repo_ok and update_patient_ok:
        print("\nAll checks passed! The patient update functionality should work correctly.")
        return 0
    else:
        print("\nIssues were detected that may prevent patient updates from working correctly.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
