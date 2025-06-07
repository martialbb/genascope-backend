"""
This script ensures the Patient model includes the email attribute.
"""
import os
import sys

def fix_patient_model():
    # Path to the Patient model file (considering we might be running from different directories)
    # Try different possible locations
    possible_paths = [
        os.path.join(os.getcwd(), "app", "models", "patient.py"),  # If run from backend dir
        os.path.join(os.getcwd(), "backend", "app", "models", "patient.py"),  # If run from project root
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models", "patient.py")  # Absolute path from script location
    ]
    
    patient_model_path = None
    for path in possible_paths:
        if os.path.exists(path):
            patient_model_path = path
            break
    
    if not patient_model_path:
        print(f"Error: Patient model file not found. Tried paths: {possible_paths}")
        return False
    
    # Read the current content of the file
    with open(patient_model_path, 'r') as file:
        content = file.read()
    
    # Check if email is already in the model
    if "email = Column" in content:
        print("Email column already defined in Patient model.")
        return True
    
    # Add email column to the model
    lines = content.split('\n')
    insert_pos = -1
    
    # Find the appropriate position to insert the email field
    for i, line in enumerate(lines):
        if "class Patient" in line:
            # Find the position after __tablename__ line
            for j in range(i+1, len(lines)):
                if "Column" in lines[j]:
                    insert_pos = j + 1
                    break
    
    if insert_pos > 0:
        # Need to ensure String is imported
        if "from sqlalchemy import" in content:
            if "String" not in content.split("from sqlalchemy import")[1].split("\n")[0]:
                # Add String to the imports
                for i, line in enumerate(lines):
                    if "from sqlalchemy import" in line and "String" not in line:
                        lines[i] = line.rstrip() + ", String"
                        break
        
        # Insert the email column definition
        lines.insert(insert_pos, "    email = Column(String(255), nullable=True, index=True)")
        
        # Write back to the file
        with open(patient_model_path, 'w') as file:
            file.write('\n'.join(lines))
        
        print("Added email column to Patient model.")
        return True
    else:
        print("Couldn't find appropriate position to insert email column.")
        return False

if __name__ == "__main__":
    if fix_patient_model():
        print("Patient model updated successfully!")
        sys.exit(0)
    else:
        print("Failed to update Patient model.")
        sys.exit(1)