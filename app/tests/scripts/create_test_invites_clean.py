#!/usr/bin/env python3
"""
Create test invites to verify role-based access control
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

CLINICIAN_CREDENTIALS = {
    "email": "clinician@test.com", 
    "password": "admin123"
}

def login(credentials):
    """Login and return auth headers"""
    # Use form data instead of JSON for OAuth2PasswordRequestForm
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

def get_patients(headers):
    """Get list of patients"""
    response = requests.get(f"{BASE_URL}/api/patients", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get patients: {response.status_code} - {response.text}")
        return []

def get_current_user(headers):
    """Get current user info"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get current user: {response.status_code} - {response.text}")
        return None

def create_invite(headers, patient_id, email, provider_id, custom_message="Test invite"):
    """Create a test invite"""
    invite_data = {
        "patient_id": patient_id,
        "email": email,  # This should be ignored by the backend in favor of patient.email
        "provider_id": provider_id,
        "custom_message": custom_message
    }
    
    print(f"Creating invite for patient {patient_id} with email {email}...")
    print(f"Invite data: {json.dumps(invite_data, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/api/generate_invite", json=invite_data, headers=headers)
    print(f"Invite response: {response.status_code}")
    
    if response.status_code == 201 or response.status_code == 200:
        invite = response.json()
        print(f"✅ Created invite: {invite}")
        return invite
    else:
        print(f"❌ Failed to create invite for {email}: {response.status_code} - {response.text}")
        return None

def main():
    print("🧪 Creating Test Invites for Security Verification")
    print("=" * 60)
    
    # Login as admin
    print("\n🔑 Logging in as admin...")
    admin_headers = login(ADMIN_CREDENTIALS)
    if not admin_headers:
        print("❌ Failed to login as admin")
        return
    
    # Get admin user info
    print("👤 Getting admin user info...")
    admin_user = get_current_user(admin_headers)
    if not admin_user:
        print("❌ Failed to get admin user info")
        return
    admin_id = admin_user["id"]
    print(f"Admin ID: {admin_id}")
    
    # Get patients for admin's account
    print("📋 Getting patients for admin's account...")
    admin_patients = get_patients(admin_headers)
    print(f"Found {len(admin_patients)} patients for admin")
    
    if admin_patients:
        # Create invites as admin
        print("\n📧 Creating invites as admin...")
        
        # Find patients without pending invites and with valid emails
        available_patients = [
            p for p in admin_patients 
            if not p.get("has_pending_invite", False) 
            and p.get("email") 
            and p.get("email") not in ["unknown@example.com", "test@example.com"]
            and p.get("email") != None
        ]
        patient_info = [f"{p['first_name']} {p['last_name']} ({p['email']})" for p in available_patients]
        print(f"Available patients for admin: {patient_info}")
        
        if not available_patients:
            print("⚠️  No patients with valid emails and no pending invites, will skip admin invite creation")
        else:
            for i, patient in enumerate(available_patients[:2]):  # Create up to 2 invites
                email = f"testpatient{i+1}@example.com"
                print(f"Using patient: {patient['first_name']} {patient['last_name']} (ID: {patient['id']}, Email: {patient['email']})")
                create_invite(admin_headers, patient["id"], email, admin_id, f"Admin invite #{i+1}")
    
    # Login as clinician
    print("\n🔑 Logging in as clinician...")
    clinician_headers = login(CLINICIAN_CREDENTIALS)
    if not clinician_headers:
        print("❌ Failed to login as clinician")
        return
    
    # Get clinician user info
    print("👤 Getting clinician user info...")
    clinician_user = get_current_user(clinician_headers)
    if not clinician_user:
        print("❌ Failed to get clinician user info")
        return
    clinician_id = clinician_user["id"]
    print(f"Clinician ID: {clinician_id}")
    
    # Get patients (should be same account as admin)
    print("📋 Getting patients for clinician's account...")
    clinician_patients = get_patients(clinician_headers)
    print(f"Found {len(clinician_patients)} patients for clinician")
    
    if clinician_patients:
        # Create invites as clinician
        print("\n📧 Creating invites as clinician...")
        
        # Find patients without pending invites and with valid emails
        available_patients = [
            p for p in clinician_patients 
            if not p.get("has_pending_invite", False) 
            and p.get("email") 
            and p.get("email") not in ["unknown@example.com", "test@example.com"]
            and p.get("email") != None
        ]
        if not available_patients:
            print("⚠️  No patients with valid emails and no pending invites, will skip clinician invite creation")
        else:
            for i, patient in enumerate(available_patients[:1]):  # Create 1 invite
                email = f"clinicianpatient{i+1}@example.com"
                create_invite(clinician_headers, patient["id"], email, clinician_id, f"Clinician invite #{i+1}")
    
    print(f"\n🏁 Test invite creation completed!")
    print("Now run verify_invite_security.py to test role-based access control")

if __name__ == "__main__":
    main()
