"""
Test script to verify that imports work correctly.
"""
from app.models.patient import Patient
from app.models.invite import PatientInvite

def test_imports():
    """
    Test that we can import both models without circular import errors.
    """
    print("Successfully imported Patient model")
    print("Successfully imported PatientInvite model")
    print("No circular import errors detected!")

if __name__ == "__main__":
    test_imports()
