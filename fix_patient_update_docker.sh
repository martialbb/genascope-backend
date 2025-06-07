#!/bin/bash
# Script to fix the patient update functionality in Docker

# Create a Python script inside the container
cat > /tmp/fix_patient.py << 'EOF'
import sys
import json

from app.db.database import SessionLocal
from app.services.patients import PatientService
from app.repositories.invites import InviteRepository
from app.models.patient import Patient

def test_update():
    """Test the patient update flow with a sample patient"""
    print("Testing patient update functionality...")
    
    db = SessionLocal()
    try:
        # Get the first patient as a test case
        patients = db.query(Patient).limit(1).all()
        if not patients:
            print("No patients found to test with!")
            return False
            
        test_patient = patients[0]
        print(f"Using test patient: {test_patient.id} ({test_patient.first_name} {test_patient.last_name})")
        
        # Test the InviteRepository's get_by_patient_id method
        invite_repo = InviteRepository(db)
        try:
            invites = invite_repo.get_by_patient_id(test_patient.id)
            print(f"InviteRepository.get_by_patient_id works! Found {len(invites)} invites.")
        except Exception as e:
            print(f"ERROR: InviteRepository.get_by_patient_id failed: {e}")
            return False
            
        # Test the PatientService.update_patient method
        patient_service = PatientService(db)
        try:
            # Create a simple update that doesn't change anything
            update_data = {
                "first_name": test_patient.first_name,
                "last_name": test_patient.last_name
            }
            updated_patient = patient_service.update_patient(test_patient.id, update_data)
            print(f"PatientService.update_patient works!")
            return True
        except Exception as e:
            print(f"ERROR: PatientService.update_patient failed: {e}")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_update()
    sys.exit(0 if success else 1)
EOF

# Run the script
echo "Running patient update test script..."
python /tmp/fix_patient.py
result=$?

if [ $result -eq 0 ]; then
    echo -e "\n✅ Patient update functionality is working correctly!"
else
    echo -e "\n❌ Patient update functionality is NOT working correctly!"
    echo "Manual inspection required."
fi

exit $result
