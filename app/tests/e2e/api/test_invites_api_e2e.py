#!/usr/bin/env python3
"""
End-to-End test script for Invite API endpoints.
Tests all invite-related API functionality.
"""
import requests
import json
from datetime import datetime, date, timedelta
import sys
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"
AUTH_API = f"{BASE_URL}/api/auth"

# Test credentials
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "test123"
CLINICIAN_EMAIL = "clinician@test.com"
CLINICIAN_PASSWORD = "test123"

def get_auth_token(email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    """Get authentication token for API requests."""
    auth_data = {
        "username": email,
        "password": password
    }
    
    response = requests.post(f"{AUTH_API}/token", data=auth_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return None

def create_test_patient(headers, clinician_id, suffix=""):
    """Create a test patient for invites."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    patient_data = {
        "first_name": "Test",
        "last_name": "Patient",
        "email": f"invite.patient.{timestamp}{suffix}@example.com",
        "phone": "+1234567890",
        "date_of_birth": "1990-01-01",
        "status": "active",
        "clinician_id": clinician_id
    }
    
    response = requests.post(f"{BASE_URL}/api/patients/", json=patient_data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to create test patient: {response.status_code} - {response.text}")
        return None

def get_clinician_id(headers):
    """Get a clinician ID for testing."""
    response = requests.get(f"{API_BASE}/clinicians", headers=headers)
    if response.status_code == 200:
        clinicians = response.json()
        if clinicians:
            return clinicians[0]["id"]
    return None

def get_current_user_id(headers):
    """Get current user's ID."""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        return user["id"]
    return None

def test_invite_api_endpoints():
    """Test all invite API endpoints comprehensively."""
    print("🧪 Testing Invite API Endpoints")
    print("=" * 50)
    
    # Get authentication tokens
    print("1. Authenticating...")
    admin_token = get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_token:
        print("❌ Failed to authenticate admin user")
        return False
    
    clinician_token = get_auth_token(CLINICIAN_EMAIL, CLINICIAN_PASSWORD)
    if not clinician_token:
        print("❌ Failed to authenticate clinician user")
        return False
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    clinician_headers = {"Authorization": f"Bearer {clinician_token}"}
    
    print("✅ Authentication successful")
    
    # Get clinician ID first
    print("\n2. Getting clinician ID...")
    clinician_id = get_clinician_id(admin_headers)
    if not clinician_id:
        print("❌ Failed to get clinician ID")
        return False
    print(f"✅ Clinician ID: {clinician_id}")
    
    # Create test patient
    print("\n3. Creating test patient...")
    test_patient = create_test_patient(admin_headers, clinician_id, "")
    if not test_patient:
        return False
    
    patient_id = test_patient["id"]
    print(f"✅ Test patient created: {patient_id}")
    
    # Variables to store created resources for cleanup
    created_invites = []
    
    try:
        # Test 1: Generate invite
        print("\n4. Testing generate invite...")
        invite_data = {
            "provider_id": clinician_id,  # Use clinician as provider
            "patient_id": patient_id,
            "send_email": False,  # Don't send actual emails in test
            "custom_message": "Welcome to our healthcare platform!",
            "expiry_days": 14
        }
        
        response = requests.post(f"{API_BASE}/generate_invite", json=invite_data, headers=admin_headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            invite = response.json()
            print(f"   Response: {json.dumps(invite, indent=2)}")
            
            # Check what ID field is available
            invite_id = None
            if "id" in invite:
                invite_id = invite["id"]
            elif "invite_id" in invite:
                invite_id = invite["invite_id"]
            
            if invite_id:
                created_invites.append(invite_id)
                print(f"✅ Invite generated: {invite_id}")
                
                # Extract token from URL for verification test
                invite_url = invite.get('invite_url', '')
                if '/invite/' in invite_url:
                    invite_token = invite_url.split('/invite/')[-1]
                else:
                    invite_token = invite.get('invite_token', 'N/A')
                
                print(f"   Token: {invite_token[:20]}...")
                print(f"   Status: {invite.get('status', 'N/A')}")
            else:
                print(f"❌ No ID found in response")
                return False
        else:
            print(f"❌ Generate invite failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Test 2: Get all invites
        print("\n5. Testing get all invites...")
        response = requests.get(f"{API_BASE}/invites", headers=admin_headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            invites_list = response.json()
            print(f"✅ Retrieved {len(invites_list.get('invites', []))} invites")
        else:
            print(f"❌ Get invites failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 3: Get invite by ID
        print("\n6. Testing get invite by ID...")
        invite_id = created_invites[0]
        response = requests.get(f"{API_BASE}/invites/{invite_id}", headers=admin_headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            invite_detail = response.json()
            print(f"✅ Retrieved invite: {invite_detail.get('invite_id', invite_detail.get('id', 'N/A'))}")
            print(f"   Patient: {invite_detail.get('first_name')} {invite_detail.get('last_name')}")
        else:
            print(f"❌ Get invite by ID failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 4: Verify invite (without registering)
        print("\n7. Testing verify invite...")
        verify_data = {
            "token": invite_token
        }
        response = requests.post(f"{API_BASE}/verify_invite", json=verify_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            verification = response.json()
            print(f"   Response: {json.dumps(verification, indent=2)}")
            print(f"✅ Invite verified successfully")
            print(f"   Valid: {verification.get('valid', verification.get('is_valid'))}")
            patient_info = verification.get('patient_info', {})
            print(f"   Patient: {patient_info.get('first_name', 'N/A')} {patient_info.get('last_name', 'N/A')}")
        else:
            print(f"❌ Verify invite failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 5: Resend invite
        print("\n8. Testing resend invite...")
        response = requests.post(f"{API_BASE}/invites/{invite_id}/resend", headers=admin_headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            resent_invite = response.json()
            print(f"✅ Invite resent successfully")
            
            # Extract new token from URL
            new_invite_url = resent_invite.get('invite_url', '')
            if '/invite/' in new_invite_url:
                new_token = new_invite_url.split('/invite/')[-1]
            else:
                new_token = resent_invite.get('invite_token', 'N/A')
            
            print(f"   New token: {new_token[:20]}...")
        else:
            print(f"❌ Resend invite failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 6: Get pending invites for clinician
        print("\n9. Testing get pending invites for clinician...")
        # Use the actual clinician's ID from their token
        actual_clinician_id = get_current_user_id(clinician_headers)
        if actual_clinician_id:
            response = requests.get(f"{API_BASE}/pending/{actual_clinician_id}", headers=clinician_headers)
        else:
            response = requests.get(f"{API_BASE}/pending/{clinician_id}", headers=clinician_headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            pending_invites = response.json()
            print(f"✅ Retrieved {len(pending_invites)} pending invites for clinician")
        else:
            print(f"❌ Get pending invites failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 7: Bulk invite creation
        print("\n10. Testing bulk invite creation...")
        # Create another test patient for bulk invite
        test_patient2 = create_test_patient(admin_headers, clinician_id, "_bulk")
        if test_patient2:
            bulk_data = {
                "patients": [
                    {
                        "patient_id": test_patient2["id"],
                        "email": test_patient2["email"],
                        "first_name": test_patient2["first_name"],
                        "last_name": test_patient2["last_name"],
                        "phone": test_patient2.get("phone")
                    }
                ],
                "provider_id": clinician_id,
                "send_email": False,
                "custom_message": "Bulk invite test message"
            }
            
            response = requests.post(f"{API_BASE}/bulk_invite", json=bulk_data, headers=admin_headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                bulk_result = response.json()
                print(f"   Response: {json.dumps(bulk_result, indent=2)}")
                print(f"✅ Bulk invite created")
                print(f"   Successful: {bulk_result.get('total_sent', 0)}")
                print(f"   Failed: {bulk_result.get('total_failed', 0)}")
                if bulk_result.get('successful'):
                    for bulk_invite in bulk_result['successful']:
                        invite_id_field = bulk_invite.get('invite_id', bulk_invite.get('id'))
                        if invite_id_field:
                            created_invites.append(invite_id_field)
            else:
                print(f"❌ Bulk invite failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        # Test 8: Get clinicians list
        print("\n11. Testing get clinicians list...")
        response = requests.get(f"{API_BASE}/clinicians", headers=admin_headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            clinicians = response.json()
            print(f"✅ Retrieved {len(clinicians)} clinicians")
        else:
            print(f"❌ Get clinicians failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 9: Error handling - Invalid invite token
        print("\n12. Testing error handling...")
        invalid_verify_data = {
            "invite_token": "invalid-token-123"
        }
        response = requests.post(f"{API_BASE}/verify_invite", json=invalid_verify_data)
        if response.status_code == 404 or response.status_code == 400:
            print("✅ 404/400 error for invalid invite token")
        else:
            print(f"⚠️ Unexpected response for invalid token: {response.status_code}")
        
        # Test 10: Revoke invite
        print("\n13. Testing revoke invite...")
        if created_invites:
            response = requests.delete(f"{API_BASE}/revoke/{created_invites[0]}", headers=admin_headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Invite revoked successfully")
            else:
                print(f"❌ Revoke invite failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        print("\n" + "=" * 50)
        print("🎉 Invite API testing completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        print("\n14. Cleaning up...")
        for invite_id in created_invites:
            try:
                requests.delete(f"{API_BASE}/revoke/{invite_id}", headers=admin_headers)
            except:
                pass
        
        # Clean up test patients
        try:
            requests.delete(f"{BASE_URL}/api/patients/{patient_id}", headers=admin_headers)
            if 'test_patient2' in locals():
                requests.delete(f"{BASE_URL}/api/patients/{test_patient2['id']}", headers=admin_headers)
        except:
            pass

if __name__ == "__main__":
    success = test_invite_api_endpoints()
    sys.exit(0 if success else 1)
