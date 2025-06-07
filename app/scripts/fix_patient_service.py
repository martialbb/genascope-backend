#!/usr/bin/env python3
"""
This script updates the PatientService to properly handle UUID to string conversion.
"""
import os
import sys
import re

def fix_patient_service():
    # Path to the patients service file
    possible_paths = [
        os.path.join(os.getcwd(), "app", "services", "patients.py"),  # If run from backend dir
        os.path.join(os.getcwd(), "backend", "app", "services", "patients.py"),  # If run from project root
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "patients.py")  # Absolute path from script location
    ]
    
    service_file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            service_file_path = path
            break
    
    if not service_file_path:
        print(f"Error: Patient service file not found. Tried paths: {possible_paths}")
        return False
    
    # Read the file content
    with open(service_file_path, 'r') as file:
        content = file.read()
    
    # Find the pattern for the patient_dict portion of search_patients_with_invite_status method
    pattern = r"""            # Convert patient to dict and add invite status
            patient_dict = \{
                "id": patient\.id,
                "email": patient\.email,
                "first_name": patient\.first_name,
                "last_name": patient\.last_name,
                "phone": patient\.phone,
                "external_id": patient\.external_id,
                "date_of_birth": patient\.date_of_birth,
                "status": patient\.status,
                "clinician_id": patient\.clinician_id,
                "account_id": patient\.account_id,
                "created_at": patient\.created_at,
                "updated_at": patient\.updated_at,
                "has_pending_invite": has_pending_invite
            \}"""
    
    # Replacement with string conversion for UUID fields
    replacement = """            # Convert patient to dict and add invite status
            patient_dict = {
                "id": str(patient.id) if patient.id else None,
                "email": patient.email if hasattr(patient, 'email') and patient.email is not None else "unknown@example.com",
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "phone": patient.phone,
                "external_id": patient.external_id if hasattr(patient, 'external_id') and patient.external_id is not None else "",
                "date_of_birth": patient.date_of_birth,
                "status": patient.status,
                "clinician_id": str(patient.clinician_id) if patient.clinician_id else None,
                "account_id": str(patient.account_id) if patient.account_id else None,
                "created_at": patient.created_at,
                "updated_at": patient.updated_at,
                "has_pending_invite": has_pending_invite
            }"""
    
    # Replace the code for search_patients_with_invite_status
    updated_content = re.sub(pattern, replacement, content)
    
    # Now update the get_patient_with_invite_status method
    get_patient_pattern = r"""        # Convert patient to dict and add invite status
        patient_dict = \{
            "id": patient\.id,
            "email": patient\.email,
            "first_name": patient\.first_name,
            "last_name": patient\.last_name,
            "phone": patient\.phone,
            "external_id": patient\.external_id,
            "date_of_birth": patient\.date_of_birth,
            "status": patient\.status,
            "clinician_id": patient\.clinician_id,
            "account_id": patient\.account_id,
            "created_at": patient\.created_at,
            "updated_at": patient\.updated_at,
            "has_pending_invite": has_pending_invite"""
    
    get_patient_replacement = """        # Convert patient to dict and add invite status with string conversion for UUID fields
        patient_dict = {
            "id": str(patient.id) if patient.id else None,
            "email": patient.email if hasattr(patient, 'email') and patient.email is not None else "unknown@example.com",
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "phone": patient.phone,
            "external_id": patient.external_id if hasattr(patient, 'external_id') and patient.external_id is not None else "",
            "date_of_birth": patient.date_of_birth,
            "status": patient.status,
            "clinician_id": str(patient.clinician_id) if patient.clinician_id else None,
            "account_id": str(patient.account_id) if patient.account_id else None,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
            "has_pending_invite": has_pending_invite"""
    
    # Apply the second replacement
    updated_content2 = re.sub(get_patient_pattern, get_patient_replacement, updated_content)
    
    # Check if anything was replaced
    if updated_content2 == content:
        print("No changes needed for patient service.")
        return True
    
    updated_content = updated_content2
    if content == updated_content:
        print("Warning: No changes were made to the file. Check your regex patterns.")
    else:
        print(f"Changes applied. Difference in content length: {len(updated_content) - len(content)} bytes")
    
    # Write back to the file
    with open(service_file_path, 'w') as file:
        file.write(updated_content)
    
    print("Fixed patient service to properly handle UUID and null values.")
    return True

if __name__ == "__main__":
    if fix_patient_service():
        print("Patient service updated successfully!")
        sys.exit(0)
    else:
        print("Failed to update patient service.")
        sys.exit(1)
