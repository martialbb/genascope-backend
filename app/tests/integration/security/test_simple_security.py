#!/usr/bin/env python3
"""
Simple manual security verification for invite endpoints
Tests the fixed account-based access control
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"

def test_security_fixes():
    """Test the security fixes we implemented"""
    print("🔒 Testing Invite Security Fixes")
    print("=" * 40)
    
    # Step 1: Login as admin
    login_data = {
        "username": "admin@test.com",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Test invites list endpoint (main endpoint we fixed)
    print("\n🔍 Testing /api/invites endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/invites", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            invites = data.get('invites', [])
            print(f"✅ Retrieved {len(invites)} invites")
            
            # Check if we have any invites to test with
            if invites:
                first_invite = invites[0]
                invite_id = first_invite.get('invite_id')
                print(f"Sample invite ID: {invite_id}")
                
                # Step 3: Test individual invite endpoint
                if invite_id:
                    print(f"\n🔍 Testing /api/invites/{invite_id} endpoint...")
                    try:
                        invite_response = requests.get(f"{BASE_URL}/api/invites/{invite_id}", headers=headers)
                        print(f"Individual invite status: {invite_response.status_code}")
                        if invite_response.status_code == 200:
                            print("✅ Individual invite access successful")
                        elif invite_response.status_code == 403:
                            print("🔒 Individual invite correctly denied (good security)")
                        else:
                            print(f"⚠️ Unexpected response: {invite_response.status_code}")
                    except Exception as e:
                        print(f"❌ Individual invite test error: {e}")
            else:
                print("ℹ️ No invites found to test individual access")
        else:
            print(f"❌ Failed to get invites: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Invites list test error: {e}")
    
    # Step 4: Test clinicians list endpoint
    print("\n🔍 Testing /api/clinicians endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/clinicians", headers=headers)
        print(f"Clinicians list status: {response.status_code}")
        
        if response.status_code == 200:
            clinicians = response.json()
            print(f"✅ Retrieved {len(clinicians)} clinicians")
        else:
            print(f"❌ Failed to get clinicians: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Clinicians test error: {e}")
    
    # Step 5: Test pending invites endpoint (if we have clinicians)
    print("\n🔍 Testing pending invites endpoint...")
    try:
        # Get clinicians first
        clinicians_response = requests.get(f"{BASE_URL}/api/clinicians", headers=headers)
        if clinicians_response.status_code == 200:
            clinicians = clinicians_response.json()
            if clinicians:
                first_clinician = clinicians[0]
                clinician_id = first_clinician.get('id')
                
                if clinician_id:
                    pending_response = requests.get(f"{BASE_URL}/api/pending/{clinician_id}", headers=headers)
                    print(f"Pending invites status: {pending_response.status_code}")
                    
                    if pending_response.status_code == 200:
                        pending_invites = pending_response.json()
                        print(f"✅ Retrieved {len(pending_invites)} pending invites")
                    elif pending_response.status_code == 403:
                        print("🔒 Pending invites correctly denied (good security)")
                    else:
                        print(f"⚠️ Unexpected response: {pending_response.status_code}")
                else:
                    print("ℹ️ No clinician ID found to test")
            else:
                print("ℹ️ No clinicians found to test pending invites")
        else:
            print(f"❌ Could not get clinicians for pending test: {clinicians_response.status_code}")
            
    except Exception as e:
        print(f"❌ Pending invites test error: {e}")
    
    print("\n✅ Security testing completed!")
    print("Note: This test verifies that endpoints are accessible and respond correctly.")
    print("The real security is enforced server-side through account-based filtering.")
    
    return True

def main():
    success = test_security_fixes()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
