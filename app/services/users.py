from typing import Dict, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

class UserService:
    """
    Service for user-related operations
    """
    def __init__(self, db: Session):
        self.db = db
    
    def get_clinician_name(self, clinician_id: str) -> str:
        """
        Get the name of a clinician by ID
        
        In a real implementation, this would query the user database
        """
        # Mock clinician data - would come from database
        clinician_names = {
            "clinician1": "Dr. Jane Smith",
            "clinician2": "Dr. John Davis",
            "clinician-123": "Dr. Test Doctor"
        }
        return clinician_names.get(clinician_id, "Unknown Doctor")
    
    def get_patient_name(self, patient_id: str) -> str:
        """
        Get the name of a patient by ID
        
        In a real implementation, this would query the user database
        """
        # Mock patient data - would come from database
        patient_names = {
            "patient1": "John Doe",
            "patient2": "Jane Smith",
            "patient-123": "Test Patient"
        }
        return patient_names.get(patient_id, "Unknown Patient")
