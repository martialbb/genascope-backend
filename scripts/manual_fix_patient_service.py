#!/usr/bin/env python3
"""
This script directly updates the patients.py file in the Docker container.
"""
from datetime import datetime
import os
import sys

def fix_container_file():
    """
    Create a fixed version of the patients.py service file.
    """
    # Write a temporary edited version
    with open("/tmp/fixed_patients.py", "w") as f:
        f.write('''"""
Patient service module for business logic related to patient operations.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.repositories.patients import PatientRepository
from app.repositories.invites import InviteRepository
from app.services.base import BaseService
from app.models.patient import Patient, PatientStatus
import uuid


class PatientService(BaseService):
    """
    Service for patient operations
    """
    def __init__(self, db: Session):
        self.db = db
        self.patient_repository = PatientRepository(db)
        self.invite_repository = InviteRepository(db)
    
    def create_patient(self, patient_data: Dict[str, Any]) -> Patient:
        """
        Create a new patient record
        """
        # Check if patient already exists with this email
        existing_patient = self.patient_repository.get_by_email(patient_data["email"])
        if existing_patient:
            raise HTTPException(status_code=400, detail="A patient with this email already exists")
            
        # Create patient record
        return self.patient_repository.create_patient(patient_data)
    
    def search_patients_with_invite_status(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for patients with invite status
        
        Args:
            search_params: Dictionary of search parameters
            
        Returns:
            List[Dict[str, Any]]: List of patients with invite status
        """
        patients = self.patient_repository.search_patients(
            account_id=search_params.get("account_id"),
            clinician_id=search_params.get("clinician_id"),
            query=search_params.get("query"),
            status=search_params.get("status"),
            limit=search_params.get("limit", 100),
            offset=search_params.get("offset", 0)
        )
        
        result = []
        
        for patient in patients:
            has_pending_invite = self.patient_repository.has_pending_invite(patient.id)
            
            # Convert patient to dict and add invite status
            patient_dict = {
                "id": str(patient.id) if patient.id else None,
                "email": patient.email if hasattr(patient, "email") and patient.email is not None else "unknown@example.com",
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "phone": patient.phone,
                "external_id": patient.external_id if hasattr(patient, "external_id") and patient.external_id is not None else "",
                "date_of_birth": patient.date_of_birth,
                "status": patient.status,
                "clinician_id": str(patient.clinician_id) if patient.clinician_id else None,
                "account_id": str(patient.account_id) if patient.account_id else None,
                "created_at": patient.created_at,
                "updated_at": patient.updated_at,
                "has_pending_invite": has_pending_invite
            }
            
            result.append(patient_dict)
        
        return result
    
    def get_patient_with_invite_status(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient with invite status
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Dict[str, Any]: Patient data with invite status
        """
        patient = self.patient_repository.get_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        has_pending_invite = self.patient_repository.has_pending_invite(patient_id)
        
        # Convert patient to dict and add invite status
        patient_dict = {
            "id": str(patient.id) if patient.id else None,
            "email": patient.email if hasattr(patient, "email") and patient.email is not None else "unknown@example.com",
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "phone": patient.phone,
            "external_id": patient.external_id if hasattr(patient, "external_id") and patient.external_id is not None else "",
            "date_of_birth": patient.date_of_birth,
            "status": patient.status,
            "clinician_id": str(patient.clinician_id) if patient.clinician_id else None,
            "account_id": str(patient.account_id) if patient.account_id else None,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
            "has_pending_invite": has_pending_invite
        }
        
        # Get invites for this patient
        invites = self.invite_repository.get_by_patient_id(patient_id)
        if invites:
            patient_dict["invites"] = [invite.id for invite in invites]
        
        return patient_dict
''')
    return True

if __name__ == "__main__":
    if fix_container_file():
        print("Fixed patients.py file created at /tmp/fixed_patients.py")
        print("Run 'docker cp /tmp/fixed_patients.py genascope-frontend-backend-1:/app/app/services/patients.py' to apply the fix")
        sys.exit(0)
    else:
        print("Failed to create fixed patients.py file.")
        sys.exit(1)
