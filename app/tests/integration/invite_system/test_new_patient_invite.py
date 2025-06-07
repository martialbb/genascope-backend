#!/usr/bin/env python3
"""
Create a test patient with valid email and then create an invite
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

# Test user credentials
ADMIN_CREDENTIALS = {
    "email": "admin@test.com",
    "password": "admin123"
}

def login(credentials):
    """Login and return auth headers"""
    form_data = {
        "username": credentials["email"],
        "password": credentials["password"],
        "grant_type": "password"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=form_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    else:
        print(f"Failed to login: {response.status_code} - {response.text}")
        return None

def get_current_user(headers):
    """Get current user info"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get current user: {response.status_code} - {response.text}")
        return None

def create_patient(headers, patient_data):
    """Create a new patient"""
    response = requests.post(f"{BASE_URL}/api/patients", json=patient_data, headers=headers)
    if response.status_code == 201 or response.status_code == 200:
        patient = response.json()
        print(f"✅ Created patient: {patient['first_name']} {patient['last_name']} ({patient['email']})")
        return patient
    else:
        print(f"❌ Failed to create patient: {response.status_code} - {response.text}")
        return None

def create_invite(headers, patient_id, provider_id, custom_message="Test invite"):
    """Create a test invite"""
    invite_data = {
        "patient_id": patient_id,
        "provider_id": provider_id,
        "custom_message": custom_message
    }
    
    print(f"Creating invite for patient {patient_id}...")
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

def main():
    print("🧪 Testing Invite Creation with New Patient")
    print("=" * 50)
    
    # Login as admin
    print("\n🔑 Logging in as admin...")
    headers = login(ADMIN_CREDENTIALS)
    if not headers:
        print("❌ Failed to login as admin")
        return
    
    # Get admin user info
    user = get_current_user(headers)
    if not user:
        print("❌ Failed to get admin user info")
        return
    
    admin_id = user["id"]
    account_id = user["account_id"]
    
    # Create a new patient with a valid email
    print("\n👤 Creating new patient...")
    import time
    unique_id = str(int(time.time()))
    patient_data = {
        "first_name": "Test",
        "last_name": "Patient",
        "email": f"testpatient.valid.{unique_id}@example.com",
        "phone": "+1-555-TEST-001",
        "status": "active",
        "clinician_id": admin_id,
        "account_id": account_id
    }
    
    patient = create_patient(headers, patient_data)
    if not patient:
        print("❌ Failed to create patient")
        return
    
    # Create invite for the new patient
    print(f"\n📧 Creating invite for new patient...")
    invite = create_invite(headers, patient["id"], admin_id, "Test invite for new patient")
    
    if invite:
        print(f"\n✅ Success! Invite created:")
        print(f"   Invite ID: {invite['invite_id']}")
        print(f"   Invite URL: {invite['invite_url']}")
        print(f"   Patient Email: {invite['email']}")
        print(f"   Status: {invite['status']}")
        print(f"   Expires: {invite['expires_at']}")
    else:
        print("❌ Failed to create invite")

if __name__ == "__main__":
    main()
