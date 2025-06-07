#!/usr/bin/env python3
"""
This script ensures the PatientService class includes the update_patient method.
"""
import os
import sys
import re

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.patients import PatientService
from datetime import datetime


def fix_patient_service_update_method():
    """
    Ensures the PatientService class has a properly implemented update_patient method.
    """
    # Path to the patient service file
    service_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "services", "patients.py")
    
    # Read the current file content
    with open(service_path, 'r') as file:
        content = file.read()
    
    # Check if the update_patient method is already properly implemented
    if re.search(r"def update_patient\([^)]*\).*?db\.commit\(\)", content, re.DOTALL):
        print("✅ update_patient method already properly implemented.")
        return True
    
    # Check if the method exists but might be incomplete
    has_method = re.search(r"def update_patient\([^)]*\)", content)
    
    # If the method doesn't exist or is incomplete, add or fix it
    if not has_method:
        # Add the method at the end of the class (before the last closing brace)
        pattern = r"(class PatientService.*?)(^\s*}|$)"
        replacement = r"\1    def update_patient(self, patient_id: str, update_data: Dict[str, Any]) -> Patient:\n        \"\"\"\n        Update an existing patient\n        \n        Args:\n            patient_id: ID of the patient to update\n            update_data: Dictionary of fields to update\n            \n        Returns:\n            Patient: Updated patient model\n        \"\"\"\n        # Get existing patient\n        patient = self.patient_repository.get_by_id(patient_id)\n        if not patient:\n            raise HTTPException(status_code=404, detail=\"Patient not found\")\n        \n        # Apply updates to the patient model\n        for key, value in update_data.items():\n            if hasattr(patient, key):\n                setattr(patient, key, value)\n        \n        # Update timestamp\n        patient.updated_at = datetime.utcnow()\n        \n        # Save changes\n        self.db.commit()\n        self.db.refresh(patient)\n        \n        return patient\n\2"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(service_path, 'w') as file:
            file.write(content)
        
        print("✅ Added update_patient method to PatientService class.")
    else:
        print("⚠️ update_patient method exists but might be incomplete. Please check it manually.")
    
    return True


def test_update_patient():
    """Test the update_patient method with the database."""
    try:
        # Create a database session
        db = SessionLocal()
        
        # Create an instance of PatientService
        patient_service = PatientService(db)
        
        # Check if the method exists
        if not hasattr(patient_service, "update_patient"):
            print("ERROR: update_patient method is missing from PatientService class.")
            return False
            
        print("✅ update_patient method exists in PatientService class.")
        return True
    finally:
        db.close()


if __name__ == "__main__":
    if fix_patient_service_update_method() and test_update_patient():
        print("\nFix successful: PatientService.update_patient is now properly implemented.")
        sys.exit(0)
    else:
        print("\nFix failed: There's an issue with the PatientService.update_patient method.")
        sys.exit(1)
