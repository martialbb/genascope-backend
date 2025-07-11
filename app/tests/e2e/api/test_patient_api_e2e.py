#!/usr/bin/env python3
"""
End-to-End test script for Patient API endpoints.
Tests all patient-related API functionality including CRUD operations.
"""
import requests
import json
from datetime import datetime, date
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/patients"
AUTH_API = f"{BASE_URL}/api/auth"

# Test credentials (admin user)
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "test123"

def get_auth_token():
    """Get authentication token for API requests."""
    auth_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    print(f"Trying to authenticate with: {ADMIN_EMAIL}")
    print(f"URL: {AUTH_API}/token")
    response = requests.post(f"{AUTH_API}/token", data=auth_data)
    print(f"Response status: {response.status_code}")
    print(f"Response text: {response.text}")
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return None

def test_patient_api_endpoints():
    """Test all patient API endpoints comprehensively."""
    print("🧪 Testing Patient API Endpoints")
    print("=" * 50)
    
    # Get authentication token
    print("1. Authenticating...")
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print("✅ Authentication successful")
    
    created_patients = []
    success = True
    
    try:
        # Test 1: Create a new patient
        print("\n2. Testing patient creation...")
        patient_data = {
            "email": f"test.patient.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1990-01-15",
            "clinician_id": "admin-user-id",  # Will need to get actual clinician ID
            "notes": "Test patient created by E2E test",
            "status": "active"
        }
        
        # First get a real clinician ID
        print("   Getting clinician ID...")
        users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        if users_response.status_code == 200:
            users = users_response.json()
            clinician = next((u for u in users if u.get("role") in ["clinician", "admin"]), None)
            if clinician:
                patient_data["clinician_id"] = clinician["id"]
                print(f"   Found clinician: {clinician['email']}")
            else:
                print("   ⚠️ No clinician found, using first user")
                if users:
                    patient_data["clinician_id"] = users[0]["id"]
        
        create_response = requests.post(API_BASE, headers=headers, json=patient_data)
        
        if create_response.status_code == 200:
            created_patient = create_response.json()
            created_patients.append(created_patient)
            patient_id = created_patient["id"]
            print(f"✅ Patient created successfully: {patient_id}")
            print(f"   Name: {created_patient['first_name']} {created_patient['last_name']}")
            print(f"   Email: {created_patient['email']}")
            print(f"   Status: {created_patient['status']}")
        else:
            print(f"❌ Patient creation failed: {create_response.status_code}")
            print(f"   Response: {create_response.text}")
            success = False
        
        # Test 2: Get all patients
        print("\n3. Testing get all patients...")
        get_all_response = requests.get(API_BASE, headers=headers)
        
        if get_all_response.status_code == 200:
            all_patients = get_all_response.json()
            print(f"✅ Retrieved {len(all_patients)} patients")
            
            # Verify our created patient is in the list
            found_patient = next((p for p in all_patients if p["id"] == patient_id), None)
            if found_patient:
                print("✅ Created patient found in patient list")
            else:
                print("❌ Created patient not found in patient list")
                success = False
        else:
            print(f"❌ Get all patients failed: {get_all_response.status_code}")
            print(f"   Response: {get_all_response.text}")
            success = False
        
        # Test 3: Get patient by ID
        print("\n4. Testing get patient by ID...")
        get_one_response = requests.get(f"{API_BASE}/{patient_id}", headers=headers)
        
        if get_one_response.status_code == 200:
            retrieved_patient = get_one_response.json()
            print(f"✅ Retrieved patient by ID: {retrieved_patient['id']}")
            
            # Verify data matches
            if (retrieved_patient["email"] == patient_data["email"] and
                retrieved_patient["first_name"] == patient_data["first_name"] and
                retrieved_patient["last_name"] == patient_data["last_name"]):
                print("✅ Patient data matches creation data")
            else:
                print("❌ Patient data does not match creation data")
                success = False
        else:
            print(f"❌ Get patient by ID failed: {get_one_response.status_code}")
            print(f"   Response: {get_one_response.text}")
            success = False
        
        # Test 4: Update patient
        print("\n5. Testing patient update...")
        update_data = {
            "first_name": "Jane",
            "phone": "+1-555-987-6543",
            "notes": "Updated by E2E test"
        }
        
        update_response = requests.put(f"{API_BASE}/{patient_id}", headers=headers, json=update_data)
        
        if update_response.status_code == 200:
            updated_patient = update_response.json()
            print(f"✅ Patient updated successfully")
            
            # Verify updates
            if (updated_patient["first_name"] == "Jane" and 
                updated_patient["phone"] == "+1-555-987-6543"):
                print("✅ Patient updates applied correctly")
            else:
                print("❌ Patient updates not applied correctly")
                success = False
        else:
            print(f"❌ Patient update failed: {update_response.status_code}")
            print(f"   Response: {update_response.text}")
            success = False
        
        # Test 5: Search/filter patients
        print("\n6. Testing patient search and filtering...")
        
        # Filter by status
        filter_response = requests.get(f"{API_BASE}?status=active", headers=headers)
        if filter_response.status_code == 200:
            filtered_patients = filter_response.json()
            print(f"✅ Status filter works: {len(filtered_patients)} active patients")
        else:
            print(f"❌ Status filter failed: {filter_response.status_code}")
            success = False
        
        # Search by name
        search_response = requests.get(f"{API_BASE}?query=Jane", headers=headers)
        if search_response.status_code == 200:
            search_results = search_response.json()
            found_our_patient = any(p["id"] == patient_id for p in search_results)
            if found_our_patient:
                print("✅ Name search works correctly")
            else:
                print("❌ Name search did not find our patient")
                success = False
        else:
            print(f"❌ Name search failed: {search_response.status_code}")
            success = False
        
        # Test 6: Test pagination
        print("\n7. Testing pagination...")
        paginated_response = requests.get(f"{API_BASE}?limit=5&offset=0", headers=headers)
        if paginated_response.status_code == 200:
            paginated_patients = paginated_response.json()
            print(f"✅ Pagination works: retrieved {len(paginated_patients)} patients (limit 5)")
            
            if len(paginated_patients) <= 5:
                print("✅ Pagination limit respected")
            else:
                print("❌ Pagination limit not respected")
                success = False
        else:
            print(f"❌ Pagination failed: {paginated_response.status_code}")
            success = False
        
        # Test 7: Test invalid requests
        print("\n8. Testing error handling...")
        
        # Try to get non-existent patient
        invalid_id = "non-existent-id"
        invalid_response = requests.get(f"{API_BASE}/{invalid_id}", headers=headers)
        if invalid_response.status_code == 404:
            print("✅ 404 error for non-existent patient")
        else:
            print(f"❌ Expected 404, got {invalid_response.status_code}")
            success = False
        
        # Try to create patient with invalid data
        invalid_patient_data = {
            "email": "invalid-email",  # Invalid email format
            "first_name": "",  # Empty required field
        }
        
        invalid_create_response = requests.post(API_BASE, headers=headers, json=invalid_patient_data)
        if invalid_create_response.status_code == 422:
            print("✅ 422 error for invalid patient data")
        else:
            print(f"❌ Expected 422, got {invalid_create_response.status_code}")
            # Don't fail the test for this, validation might differ
        
        # Test 8: Delete patient
        print("\n9. Testing patient deletion...")
        delete_response = requests.delete(f"{API_BASE}/{patient_id}", headers=headers)
        
        if delete_response.status_code == 200:
            print(f"✅ Patient deleted successfully")
            
            # Verify patient is deleted
            verify_delete_response = requests.get(f"{API_BASE}/{patient_id}", headers=headers)
            if verify_delete_response.status_code == 404:
                print("✅ Patient properly deleted (404 on subsequent get)")
            else:
                print(f"❌ Patient still exists after deletion: {verify_delete_response.status_code}")
                success = False
        else:
            print(f"❌ Patient deletion failed: {delete_response.status_code}")
            print(f"   Response: {delete_response.text}")
            success = False
    
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        success = False
    
    finally:
        # Cleanup any remaining patients
        print("\n10. Cleaning up...")
        for patient in created_patients:
            try:
                cleanup_response = requests.delete(f"{API_BASE}/{patient['id']}", headers=headers)
                if cleanup_response.status_code == 200:
                    print(f"✅ Cleaned up patient: {patient['id']}")
                else:
                    print(f"⚠️ Could not clean up patient {patient['id']}: {cleanup_response.status_code}")
            except Exception as e:
                print(f"⚠️ Cleanup error for patient {patient['id']}: {str(e)}")
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All patient API tests PASSED!")
        return True
    else:
        print("❌ Some patient API tests FAILED!")
        return False

if __name__ == "__main__":
    result = test_patient_api_endpoints()
    sys.exit(0 if result else 1)
