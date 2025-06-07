#!/usr/bin/env python3
"""
This script verifies the InviteRepository instance in PatientService has the correct implementation of get_by_patient_id method.
"""
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.repositories.invites import InviteRepository
from app.services.patients import PatientService


def check_and_fix_invite_repository():
    """
    Check if the InviteRepository class has the get_by_patient_id method and if it's being used correctly in PatientService.
    """
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create an instance of InviteRepository
        invite_repo = InviteRepository(db)
        
        # Check if the method exists
        if not hasattr(invite_repo, "get_by_patient_id"):
            print("ERROR: get_by_patient_id method is missing from InviteRepository class.")
            return False
            
        # Check if PatientService is using the method correctly
        patient_service = PatientService(db)
        
        # Test the method with a sample patient ID that's unlikely to exist
        test_patient_id = "test-patient-id-123456789"
        try:
            invites = patient_service.invite_repository.get_by_patient_id(test_patient_id)
            print(f"SUCCESS: get_by_patient_id method works in PatientService. Got {len(invites)} invites.")
            return True
        except Exception as e:
            print(f"ERROR: PatientService failed to use get_by_patient_id method: {str(e)}")
            return False
            
    finally:
        db.close()


if __name__ == "__main__":
    if check_and_fix_invite_repository():
        print("\nVerification successful: InviteRepository.get_by_patient_id is working correctly in PatientService.")
        sys.exit(0)
    else:
        print("\nVerification failed: There's an issue with InviteRepository.get_by_patient_id in PatientService.")
        print("Please check the PatientService initialization and InviteRepository implementation.")
        sys.exit(1)
