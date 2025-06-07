#!/usr/bin/env python3
"""
This script fixes the patients API endpoint to properly handle UUID conversions.
"""
import os
import sys
import re

def fix_patients_api():
    # Path to the patients API file (considering we might be running from different directories)
    # Try different possible locations
    possible_paths = [
        os.path.join(os.getcwd(), "app", "api", "patients.py"),  # If run from backend dir
        os.path.join(os.getcwd(), "backend", "app", "api", "patients.py"),  # If run from project root
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "api", "patients.py")  # Absolute path from script location
    ]
    
    api_file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            api_file_path = path
            break
    
    if not api_file_path:
        print(f"Error: Patients API file not found. Tried paths: {possible_paths}")
        return False
    
    # Read the current content of the file
    with open(api_file_path, 'r') as file:
        content = file.read()
    
    # Check if we need to make the fix
    if "for patient in patients_with_status:" in content and "patient['id'] = str(patient['id'])" not in content:
        # Find the part where the patients are converted to PatientResponse
        pattern = r"patient_responses\s*=\s*\[PatientResponse\(\*\*patient\)\s*for\s*patient\s*in\s*patients_with_status\]"
        
        replacement = """# Convert patients data to proper format with string conversion for UUID fields
        for patient in patients_with_status:
            if patient.get('id') and not isinstance(patient.get('id'), str):
                patient['id'] = str(patient.get('id', ''))
            if patient.get('clinician_id') and not isinstance(patient.get('clinician_id'), str):
                patient['clinician_id'] = str(patient.get('clinician_id', ''))
            if patient.get('account_id') and not isinstance(patient.get('account_id'), str):
                patient['account_id'] = str(patient.get('account_id', ''))
            # Ensure email has a default value if missing
            if patient.get('email') is None:
                patient['email'] = ''
            # Ensure external_id has a default value if missing
            if patient.get('external_id') is None:
                patient['external_id'] = ''
        
        patient_responses = [PatientResponse(**patient) for patient in patients_with_status]"""
        
        # Replace the code
        updated_content = re.sub(pattern, replacement, content)
        
        # Write back to the file
        with open(api_file_path, 'w') as file:
            file.write(updated_content)
        
        print("Fixed patients API endpoint for proper UUID conversions.")
        return True
    else:
        print("No changes needed for patients API endpoint.")
        return True

if __name__ == "__main__":
    if fix_patients_api():
        print("Patients API endpoint fixed successfully!")
        sys.exit(0)
    else:
        print("Failed to fix patients API endpoint.")
        sys.exit(1)
