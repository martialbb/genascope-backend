#!/usr/bin/env python3
"""
End-to-End Test Script for Eligibility API

This script tests all eligibility endpoints to ensure they work correctly:
1. Authentication
2. Analyze eligibility (POST)
3. Get eligibility analysis (GET)
4. Get detailed eligibility results
5. Comprehensive eligibility assessment
6. Get patient recommendations
7. Get eligibility summary
8. Error handling
9. Authentication requirements
"""
import requests
import json
import sys
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/auth"
ELIGIBILITY_URL = f"{BASE_URL}/api/eligibility"

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

def get_test_patient(headers):
    """Get a test patient for eligibility analysis"""
    print(f"3. Getting test patient...")
    
    # Try to get patients
    response = requests.get(f"{BASE_URL}/api/patients", headers=headers)
    if response.status_code == 200:
        patients = response.json()
        if patients:
            patient = patients[0]
            print(f"✅ Found patient: {patient.get('first_name', 'Unknown')} {patient.get('last_name', '')} ({patient['id']})")
            return patient
    
    # Fallback to known patient ID
    print("⚠️ Using known patient ID for testing")
    return {'id': '4320f725-6139-4449-95e3-14fb41da5aa1', 'first_name': 'Test', 'last_name': 'Patient'}

def test_analyze_eligibility(headers, patient_id):
    """Test POST /api/eligibility/analyze"""
    print(f"4. Testing analyze eligibility (POST)...")
    
    assessment_data = {
        "patient_id": patient_id,
        "parameters": {
            "age": 45,
            "family_history": True,
            "genetic_mutations": ["BRCA1"],
            "previous_cancer": False,
            "ashkenazi_jewish": False
        }
    }
    
    response = requests.post(f"{ELIGIBILITY_URL}/analyze", headers=headers, json=assessment_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        print(f"✅ Eligibility analysis completed successfully")
        return result
    else:
        print(f"❌ Failed to analyze eligibility: {response.text}")
        return None

def test_get_eligibility_analysis(headers, patient_id):
    """Test GET /api/eligibility/analyze/{patient_id}"""
    print(f"5. Testing get eligibility analysis (GET)...")
    
    response = requests.get(f"{ELIGIBILITY_URL}/analyze/{patient_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        print(f"✅ Eligibility analysis retrieved successfully")
        return result
    else:
        print(f"❌ Failed to get eligibility analysis: {response.text}")
        return None

def test_detailed_eligibility(headers, patient_id):
    """Test GET /api/eligibility/detailed/{patient_id}"""
    print(f"6. Testing detailed eligibility results...")
    
    response = requests.get(f"{ELIGIBILITY_URL}/detailed/{patient_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Found {len(result.get('risk_factors', []))} risk factors")
        print(f"✅ Detailed eligibility results retrieved successfully")
        return result
    else:
        print(f"❌ Failed to get detailed eligibility: {response.text}")
        return None

def test_comprehensive_assessment(headers, patient_id):
    """Test POST /api/eligibility/assess"""
    print(f"7. Testing comprehensive eligibility assessment...")
    
    assessment_data = {
        "patient_id": patient_id,
        "assessment_data": {
            "age": 50,
            "menarche_age": 12,
            "first_birth_age": 25,
            "menopause_age": None,
            "family_history_breast": True,
            "family_history_ovarian": False,
            "previous_biopsies": 0,
            "hormone_therapy": False,
            "BMI": 24.5
        },
        "chat_session_id": None
    }
    
    response = requests.post(f"{ELIGIBILITY_URL}/assess", headers=headers, json=assessment_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"   Assessment completed with {len(result.get('risk_factors', []))} risk factors")
        print(f"✅ Comprehensive assessment completed successfully")
        return result
    else:
        print(f"❌ Failed to complete assessment: {response.text}")
        return None

def test_patient_recommendations(headers, patient_id):
    """Test GET /api/eligibility/recommendations/{patient_id}"""
    print(f"8. Testing patient recommendations...")
    
    response = requests.get(f"{ELIGIBILITY_URL}/recommendations/{patient_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        recommendations = response.json()
        print(f"   Found {len(recommendations)} recommendations")
        if recommendations:
            print(f"   Sample: {recommendations[0].get('recommendation_type', 'Unknown')}")
        print(f"✅ Patient recommendations retrieved successfully")
        return recommendations
    else:
        print(f"❌ Failed to get recommendations: {response.text}")
        return None

def test_eligibility_summary(headers, patient_id):
    """Test GET /api/eligibility/summary/{patient_id}"""
    print(f"9. Testing eligibility summary...")
    
    response = requests.get(f"{ELIGIBILITY_URL}/summary/{patient_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        summary = response.json()
        print(f"   Overall eligible: {summary.get('overall_eligible', 'Unknown')}")
        print(f"✅ Eligibility summary retrieved successfully")
        return summary
    else:
        print(f"❌ Failed to get eligibility summary: {response.text}")
        return None

def test_error_handling(headers):
    """Test error handling for invalid requests"""
    print(f"10. Testing error handling...")
    
    # Test invalid patient ID
    response = requests.get(f"{ELIGIBILITY_URL}/analyze/invalid-patient-id", headers=headers)
    if response.status_code in [400, 404, 422]:
        print(f"✅ 400/404/422 error for invalid patient ID")
    else:
        print(f"⚠️ Expected 400/404/422 for invalid patient, got {response.status_code}")
    
    # Test invalid assessment data
    invalid_data = {
        "patient_id": "invalid-id",
        "parameters": "invalid-format"
    }
    response = requests.post(f"{ELIGIBILITY_URL}/analyze", headers=headers, json=invalid_data)
    if response.status_code in [400, 422]:
        print(f"✅ 400/422 error for invalid assessment data")
    else:
        print(f"⚠️ Expected 400/422 for invalid data, got {response.status_code}")

def test_authentication_requirements():
    """Test that endpoints require authentication"""
    print(f"11. Testing authentication requirements...")
    
    # Test without authorization header
    response = requests.get(f"{ELIGIBILITY_URL}/summary/test-patient-id")
    if response.status_code == 401:
        print(f"✅ 401 error when no authentication provided")
    else:
        print(f"⚠️ Expected 401 when no auth, got {response.status_code}")
    
    # Test with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{ELIGIBILITY_URL}/summary/test-patient-id", headers=invalid_headers)
    if response.status_code == 401:
        print(f"✅ 401 error for invalid token")
    else:
        print(f"⚠️ Expected 401 for invalid token, got {response.status_code}")

def main():
    print("🧬 Testing Eligibility API Endpoints")
    print("=" * 50)
    
    # Step 1: Authenticate
    access_token = authenticate()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Get current user info
    current_user = get_current_user(headers)
    
    # Step 3: Get test patient
    patient = get_test_patient(headers)
    patient_id = patient['id']
    
    try:
        # Step 4: Test analyze eligibility (POST)
        analyze_result = test_analyze_eligibility(headers, patient_id)
        
        # Step 5: Test get eligibility analysis (GET)
        get_result = test_get_eligibility_analysis(headers, patient_id)
        
        # Step 6: Test detailed eligibility
        detailed_result = test_detailed_eligibility(headers, patient_id)
        
        # Step 7: Test comprehensive assessment
        assessment_result = test_comprehensive_assessment(headers, patient_id)
        
        # Step 8: Test patient recommendations
        recommendations = test_patient_recommendations(headers, patient_id)
        
        # Step 9: Test eligibility summary
        summary = test_eligibility_summary(headers, patient_id)
        
        # Step 10: Test error handling
        test_error_handling(headers)
        
        # Step 11: Test authentication requirements
        test_authentication_requirements()
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("🎉 Eligibility API testing completed!")

if __name__ == "__main__":
    main()
