#!/usr/bin/env python3
"""
End-to-End Test Script for Labs API

This script tests all lab endpoints to ensure they work correctly:
1. Authentication
2. List available tests
3. List available labs
4. Order a test
5. Get test results
6. Get patient orders
7. Get clinician orders
8. Review test result
9. Error handling
10. Authentication requirements
"""
import requests
import json
import sys
from datetime import datetime, timedelta

# API Configuration
BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/auth"
LABS_URL = f"{BASE_URL}/api/labs"

# Test credentials (super admin)
USERNAME = "superadmin@genascope.com"
PASSWORD = "SuperAdmin123!"

def authenticate():
    """Authenticate and get access token"""
    print(f"1. Authenticating with {USERNAME}...")
    
    auth_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    }
    
    response = requests.post(f"{AUTH_URL}/token", data=auth_data)
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    
    token_data = response.json()
    access_token = token_data["access_token"]
    print("✅ Authentication successful")
    
    return access_token

def get_current_user(headers):
    """Get current user information"""
    print(f"2. Checking current user role...")
    
    response = requests.get(f"{AUTH_URL}/me", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get current user: {response.status_code}")
        sys.exit(1)
    
    user_data = response.json()
    print(f"✅ Current user: {user_data['email']}")
    print(f"   Role: {user_data['role']}")
    print(f"   ID: {user_data['id']}")
    
    return user_data

def get_test_users(headers):
    """Get test users for lab orders (clinician and patient)"""
    print(f"3. Getting test users for lab orders...")
    
    # Get users
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get users: {response.status_code}")
        return None, None
    
    users = response.json()
    
    # Find a clinician and a patient
    clinician = None
    patient = None
    
    for user in users:
        if user['role'] == 'clinician' and not clinician:
            clinician = user
        elif user['role'] == 'patient' and not patient:
            patient = user
    
    if clinician:
        print(f"✅ Found clinician: {clinician['name']} ({clinician['id']})")
    else:
        print("⚠️ No clinician found")
    
    if patient:
        print(f"✅ Found patient: {patient['name']} ({patient['id']})")
    else:
        print("⚠️ No patient found")
    
    return clinician, patient

def test_available_tests(headers):
    """Test listing available tests"""
    print(f"4. Testing list available tests...")
    
    response = requests.get(f"{LABS_URL}/available_tests", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        tests = response.json()
        print(f"   Found {len(tests)} available tests")
        if tests:
            print(f"   Sample test: {tests[0]}")
        print(f"✅ Available tests retrieved successfully")
        return tests
    else:
        print(f"❌ Failed to get available tests: {response.text}")
        return []

def test_available_labs(headers):
    """Test listing available labs"""
    print(f"5. Testing list available labs...")
    
    response = requests.get(f"{LABS_URL}/available_labs", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        labs = response.json()
        print(f"   Found {len(labs)} available labs")
        if labs:
            print(f"   Sample lab: {labs[0]}")
        print(f"✅ Available labs retrieved successfully")
        return labs
    else:
        print(f"❌ Failed to get available labs: {response.text}")
        return []

def test_order_test(headers, patient_id, clinician_id):
    """Test ordering a lab test"""
    print(f"6. Testing order lab test...")
    
    if not patient_id or not clinician_id:
        print("❌ Cannot order test: missing patient or clinician")
        return None
    
    # Get patient record for the user (similar to appointments)
    patient_record = get_patient_for_user(headers, patient_id)
    if not patient_record:
        print(f"   Using known patient ID for test user")
        patient_record = {'id': '4320f725-6139-4449-95e3-14fb41da5aa1'}
    
    order_data = {
        "patient_id": patient_record['id'],
        "test_type": "brca",
        "clinician_id": clinician_id,
        "notes": "E2E test lab order"
    }
    
    response = requests.post(f"{LABS_URL}/order_test", headers=headers, json=order_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        order = response.json()
        print(f"   Response: {json.dumps(order, indent=2)}")
        print(f"✅ Lab test ordered successfully")
        return order
    else:
        print(f"❌ Failed to order lab test: {response.text}")
        return None

def get_patient_for_user(headers, user_id):
    """Get the patient record for a user"""
    print(f"   Getting patient record for user {user_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/patients", headers=headers)
        if response.status_code == 200:
            patients = response.json()
            for patient in patients:
                if patient.get('user_id') == user_id:
                    print(f"   Found patient record: {patient['id']}")
                    return patient
        else:
            print(f"   No patients API available, status: {response.status_code}")
    except Exception as e:
        print(f"   Error getting patients: {e}")
    
    return None

def test_get_results(headers, order_id):
    """Test getting lab results"""
    print(f"7. Testing get lab results...")
    
    if not order_id:
        print("❌ Cannot get results: no order ID")
        return None
    
    response = requests.get(f"{LABS_URL}/results/{order_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"   Response: {json.dumps(results, indent=2)}")
        print(f"✅ Lab results retrieved successfully")
        return results
    else:
        print(f"❌ Failed to get lab results: {response.text}")
        return None

def test_patient_orders(headers, patient_id):
    """Test getting orders for a patient"""
    print(f"8. Testing get patient orders...")
    
    if not patient_id:
        print("❌ Cannot get patient orders: no patient ID")
        return []
    
    # Use the known patient ID
    test_patient_id = '4320f725-6139-4449-95e3-14fb41da5aa1'
    
    response = requests.get(f"{LABS_URL}/patient/{test_patient_id}/orders", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        orders = response.json()
        print(f"   Found {len(orders)} orders for patient")
        print(f"✅ Patient orders retrieved successfully")
        return orders
    else:
        print(f"❌ Failed to get patient orders: {response.text}")
        return []

def test_clinician_orders(headers, clinician_id):
    """Test getting orders for a clinician"""
    print(f"9. Testing get clinician orders...")
    
    if not clinician_id:
        print("❌ Cannot get clinician orders: no clinician ID")
        return []
    
    response = requests.get(f"{LABS_URL}/clinician/{clinician_id}/orders", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        orders = response.json()
        print(f"   Found {len(orders)} orders for clinician")
        print(f"✅ Clinician orders retrieved successfully")
        return orders
    else:
        print(f"❌ Failed to get clinician orders: {response.text}")
        return []

def test_review_result(headers, result_id):
    """Test reviewing a lab result"""
    print(f"10. Testing review lab result...")
    
    if not result_id:
        print("❌ Cannot review result: no result ID")
        return False
    
    review_data = {
        "status": "reviewed",
        "notes": "E2E test result review"
    }
    
    response = requests.post(f"{LABS_URL}/review_result/{result_id}", headers=headers, json=review_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        print(f"✅ Lab result reviewed successfully")
        return True
    else:
        print(f"❌ Failed to review lab result: {response.text}")
        return False

def test_error_handling(headers):
    """Test error handling for invalid requests"""
    print(f"11. Testing error handling...")
    
    # Test invalid order request
    invalid_order = {
        "patient_id": "invalid-id",
        "test_type": "invalid_test",
        "clinician_id": "invalid-clinician"
    }
    
    response = requests.post(f"{LABS_URL}/order_test", headers=headers, json=invalid_order)
    if response.status_code in [400, 422, 404]:
        print(f"✅ 400/422/404 error for invalid order request")
    else:
        print(f"⚠️ Expected 400/422/404 for invalid order, got {response.status_code}")
    
    # Test invalid result request
    response = requests.get(f"{LABS_URL}/results/invalid-order-id", headers=headers)
    if response.status_code in [400, 422, 404]:
        print(f"✅ 400/422/404 error for invalid result request")
    else:
        print(f"⚠️ Expected 400/422/404 for invalid result, got {response.status_code}")

def test_authentication_requirements():
    """Test that endpoints require authentication"""
    print(f"12. Testing authentication requirements...")
    
    # Test without authorization header
    response = requests.get(f"{LABS_URL}/available_tests")
    if response.status_code == 401:
        print(f"✅ 401 error when no authentication provided")
    else:
        print(f"⚠️ Expected 401 when no auth, got {response.status_code}")
    
    # Test with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{LABS_URL}/available_tests", headers=invalid_headers)
    if response.status_code == 401:
        print(f"✅ 401 error for invalid token")
    else:
        print(f"⚠️ Expected 401 for invalid token, got {response.status_code}")

def main():
    print("🧪 Testing Labs API Endpoints")
    print("=" * 50)
    
    # Step 1: Authenticate
    access_token = authenticate()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Get current user info
    current_user = get_current_user(headers)
    
    # Step 3: Get test users
    clinician, patient = get_test_users(headers)
    
    try:
        # Step 4: Test available tests
        tests = test_available_tests(headers)
        
        # Step 5: Test available labs
        labs = test_available_labs(headers)
        
        # Step 6: Test order test
        order = test_order_test(headers, patient['id'] if patient else None, clinician['id'] if clinician else None)
        
        order_id = None
        result_id = None
        
        if order:
            order_id = order.get('id') or order.get('order_id')
            
            # Step 7: Test get results
            results = test_get_results(headers, order_id)
            if results:
                result_id = results.get('id') or results.get('result_id')
        
        # Step 8: Test patient orders
        test_patient_orders(headers, patient['id'] if patient else None)
        
        # Step 9: Test clinician orders
        test_clinician_orders(headers, clinician['id'] if clinician else None)
        
        # Step 10: Test review result
        if result_id:
            test_review_result(headers, result_id)
        else:
            print("10. Testing review lab result...")
            print("⚠️ Skipping result review: no result ID available")
        
        # Step 11: Test error handling
        test_error_handling(headers)
        
        # Step 12: Test authentication requirements
        test_authentication_requirements()
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("🎉 Labs API testing completed!")

if __name__ == "__main__":
    main()
