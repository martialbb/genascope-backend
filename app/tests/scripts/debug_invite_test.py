#!/usr/bin/env python3
"""
Debug invite creation script
"""
import requests
import json
import traceback

# API base URL
BASE_URL = "http://localhost:8000"

# Test user credentials
ADMIN_CREDENTIALS = {
    "email": "admin@test.com",
    "password": "admin123"
}

def login(credentials):
    """Login and return auth headers"""
    try:
        print(f"Attempting to login with {credentials['email']}")
        form_data = {
            "username": credentials["email"],
            "password": credentials["password"],
            "grant_type": "password"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/token", data=form_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"Login successful, token starts with: {token[:20] if token else 'None'}...")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"Failed to login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception during login: {e}")
        traceback.print_exc()
        return None

def get_current_user(headers):
    """Get current user info"""
    try:
        print("Getting current user info...")
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"Current user response: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            print(f"Current user: {user}")
            return user
        else:
            print(f"Failed to get current user: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception getting current user: {e}")
        traceback.print_exc()
        return None

def get_patients(headers):
    """Get list of patients"""
    try:
        print("Getting patients...")
        response = requests.get(f"{BASE_URL}/api/patients", headers=headers)
        print(f"Patients response: {response.status_code}")
        
        if response.status_code == 200:
            patients = response.json()
            print(f"Found {len(patients)} patients")
            if patients:
                print(f"First patient: {patients[0]}")
            return patients
        else:
            print(f"Failed to get patients: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception getting patients: {e}")
        traceback.print_exc()
        return []

def create_invite(headers, patient_id, email, provider_id, custom_message="Test invite"):
    """Create a test invite"""
    try:
        print(f"Creating invite for {email}...")
        invite_data = {
            "patient_id": patient_id,
            "email": email,
            "provider_id": provider_id,
            "custom_message": custom_message
        }
        print(f"Invite data: {json.dumps(invite_data, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/api/generate_invite", json=invite_data, headers=headers)
        print(f"Invite response: {response.status_code}")
        
        if response.status_code == 201 or response.status_code == 200:
            invite = response.json()
            print(f"✅ Created invite: {invite}")
            return invite
        else:
            print(f"❌ Failed to create invite: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception creating invite: {e}")
        traceback.print_exc()
        return None

def main():
    print("🧪 Debug Invite Creation Test")
    print("=" * 40)
    
    try:
        # Test login
        headers = login(ADMIN_CREDENTIALS)
        if not headers:
            print("❌ Login failed")
            return
        
        # Test current user
        user = get_current_user(headers)
        if not user:
            print("❌ Failed to get user")
            return
            
        print("✅ Basic auth flow working")
        
        # Test patients
        patients = get_patients(headers)
        if not patients:
            print("❌ No patients found")
            return
            
        # Find a patient without pending invite
        available_patient = None
        for patient in patients:
            if not patient.get("has_pending_invite", False):
                available_patient = patient
                break
                
        if not available_patient:
            print("⚠️  All patients have pending invites, using first patient anyway")
            available_patient = patients[0]
        else:
            print(f"Found available patient: {available_patient['first_name']} {available_patient['last_name']}")
            
        # Test invite creation
        user_id = user["id"]
        test_email = "testinvite@example.com"
        
        create_invite(headers, available_patient["id"], test_email, user_id, "Debug test invite")
        
    except Exception as e:
        print(f"Main exception: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
