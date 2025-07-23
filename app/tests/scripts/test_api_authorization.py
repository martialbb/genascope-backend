#!/usr/bin/env python
"""
Test the actual patient update API endpoint to verify the fix.
"""
import requests
import json

# API endpoint
base_url = "http://localhost:8000/api"

# Login as admin to get token (using form data as required by OAuth2PasswordRequestForm)
login_data = {
    "username": "admin@test.com",  # Using test credentials from insert_test_data.sql
    "password": "admin123",       # Using test credentials from insert_test_data.sql
    "grant_type": "password"
}

print("=== Testing Patient Update API Authorization Fix ===")

try:
    # Login
    print("1. Logging in as admin@test.com...")
    login_response = requests.post(f"{base_url}/auth/token", data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        exit(1)
    
    token = login_response.json()["access_token"]
    print("✅ Login successful")
    
    # Get headers with token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get list of patients first
    print("\n2. Getting patient list...")
    patients_response = requests.get(f"{base_url}/patients", headers=headers)
    
    if patients_response.status_code != 200:
        print(f"❌ Get patients failed: {patients_response.status_code} - {patients_response.text}")
        exit(1)
    
    patients = patients_response.json()
    if not patients or len(patients) == 0:
        print("❌ No patients found to test with")
        exit(1)
    
    # Get the first patient
    patient = patients[0]
    patient_id = patient["id"]
    print(f"✅ Found patient to test with: {patient['first_name']} {patient['last_name']} (ID: {patient_id})")
    
    # Try to update the patient (just updating a simple field)
    print(f"\n3. Testing patient update for patient {patient_id}...")
    update_data = {
        "phone": "555-123-4567"  # Simple phone number update
    }
    
    update_response = requests.put(f"{base_url}/patients/{patient_id}", 
                                 headers=headers, 
                                 json=update_data)
    
    print(f"Response status: {update_response.status_code}")
    print(f"Response body: {update_response.text[:500]}...")
    
    if update_response.status_code == 200:
        print("✅ SUCCESS! Patient update authorized and completed!")
        print("✅ Authorization fix is working correctly!")
        updated_patient = update_response.json()
        print(f"✅ Updated phone number: {updated_patient.get('phone')}")
    elif update_response.status_code == 403:
        print("❌ FAILED! Still getting authorization error:")
        print(f"   {update_response.json().get('detail', 'Unknown error')}")
        print("❌ Authorization fix did not work")
    else:
        print(f"❌ Unexpected error: {update_response.status_code}")
        print(f"   {update_response.text}")
    
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to API server. Is it running on localhost:8000?")
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
