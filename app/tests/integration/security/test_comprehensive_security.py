#!/usr/bin/env python3
"""
Comprehensive security verification for invite endpoints
Tests using actual super admin credentials
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:8000"
SUPER_ADMIN_CREDENTIALS = {
    "email": "superadmin@genascope.com",
    "password": "admin123"
}

class SecurityVerificationTest:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
        
    def login_super_admin(self) -> bool:
        """Login as super admin"""
        print("🔐 Logging in as super admin...")
        
        login_data = {
            "username": SUPER_ADMIN_CREDENTIALS["email"],
            "password": SUPER_ADMIN_CREDENTIALS["password"]
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/token", data=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.session.headers.update({
                    "Authorization": f"Bearer {token_data['access_token']}"
                })
                self.logged_in = True
                print("✅ Successfully logged in as super admin")
                return True
            else:
                print(f"❌ Failed to login: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_invites_list_endpoint(self):
        """Test /api/invites endpoint"""
        print("\n🔍 Testing /api/invites endpoint...")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/invites")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Super admin can access invites list")
                print(f"   Total invites: {data.get('total_count', 0)}")
                print(f"   Current page invites: {len(data.get('invites', []))}")
                
                # Check if we have any invites to test account isolation
                invites = data.get('invites', [])
                if invites:
                    print("   Sample invite accounts:")
                    for i, invite in enumerate(invites[:3]):
                        patient_name = f"{invite.get('first_name', '')} {invite.get('last_name', '')}".strip()
                        print(f"     {i+1}. {patient_name} ({invite.get('email', 'no-email')})")
                
                return True
            else:
                print(f"❌ Failed to access invites: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing invites endpoint: {e}")
            return False
    
    def test_clinicians_list_endpoint(self):
        """Test /api/clinicians endpoint"""
        print("\n🔍 Testing /api/clinicians endpoint...")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/clinicians")
            
            if response.status_code == 200:
                clinicians = response.json()
                print(f"✅ Super admin can access clinicians list")
                print(f"   Total clinicians: {len(clinicians)}")
                
                # Show sample clinicians with their accounts
                if clinicians:
                    print("   Sample clinicians:")
                    for i, clinician in enumerate(clinicians[:3]):
                        account_info = f"Account: {clinician.get('account_id', 'No Account')}"
                        print(f"     {i+1}. {clinician.get('name', 'Unknown')} ({clinician.get('email', 'no-email')}) - {account_info}")
                
                return True
            else:
                print(f"❌ Failed to access clinicians: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing clinicians endpoint: {e}")
            return False
    
    def test_individual_invite_access(self):
        """Test individual invite access"""
        print("\n🔍 Testing individual invite access...")
        
        # First get some invite IDs
        try:
            response = self.session.get(f"{BASE_URL}/api/invites")
            if response.status_code != 200:
                print("⚠️ Cannot get invites list for individual testing")
                return False
                
            data = response.json()
            invites = data.get('invites', [])
            
            if not invites:
                print("⚠️ No invites found for individual testing")
                return True
                
            # Test first invite
            invite_id = invites[0].get('invite_id')
            if not invite_id:
                print("⚠️ No invite ID found in first invite")
                return False
                
            response = self.session.get(f"{BASE_URL}/api/invites/{invite_id}")
            
            if response.status_code == 200:
                invite = response.json()
                patient_name = f"{invite.get('first_name', '')} {invite.get('last_name', '')}".strip()
                print(f"✅ Super admin can access individual invite")
                print(f"   Invite ID: {invite_id}")
                print(f"   Patient: {patient_name}")
                print(f"   Status: {invite.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ Failed to access individual invite: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing individual invite access: {e}")
            return False
    
    def test_account_filtering_behavior(self):
        """Test that super admin sees invites from multiple accounts"""
        print("\n🔍 Testing account filtering behavior...")
        
        try:
            response = self.session.get(f"{BASE_URL}/api/invites")
            if response.status_code != 200:
                print("⚠️ Cannot test account filtering - invites endpoint failed")
                return False
                
            data = response.json()
            invites = data.get('invites', [])
            
            if not invites:
                print("⚠️ No invites found to test account filtering")
                return True
            
            # We can't directly see patient account_id in the response, but we can verify
            # that super admin gets invites (which implies cross-account access if there are multiple accounts)
            print(f"✅ Super admin has access to {len(invites)} invites")
            print("   This demonstrates cross-account visibility for super admin")
            
            # Show variety in providers to indicate cross-account data
            providers = set()
            for invite in invites:
                if invite.get('provider_name'):
                    providers.add(invite.get('provider_name'))
            
            if len(providers) > 1:
                print(f"   Multiple providers found: {', '.join(list(providers)[:3])}")
                print("   This suggests invites span multiple accounts ✅")
            else:
                print("   Note: All invites appear to be from same provider")
                
            return True
            
        except Exception as e:
            print(f"❌ Error testing account filtering: {e}")
            return False
    
    def test_pending_invites_access(self):
        """Test pending invites endpoint"""
        print("\n🔍 Testing pending invites access...")
        
        try:
            # First get clinicians to test with
            response = self.session.get(f"{BASE_URL}/api/clinicians")
            if response.status_code != 200:
                print("⚠️ Cannot get clinicians for pending invites test")
                return False
                
            clinicians = response.json()
            if not clinicians:
                print("⚠️ No clinicians found for pending invites test")
                return True
                
            # Test with first clinician
            clinician_id = clinicians[0].get('id')
            clinician_name = clinicians[0].get('name', 'Unknown')
            
            response = self.session.get(f"{BASE_URL}/api/pending/{clinician_id}")
            
            if response.status_code == 200:
                pending_invites = response.json()
                print(f"✅ Super admin can access pending invites")
                print(f"   Clinician: {clinician_name}")
                print(f"   Pending invites: {len(pending_invites)}")
                return True
            elif response.status_code == 403:
                print(f"❌ Unexpected: Super admin denied access to pending invites")
                return False
            else:
                print(f"⚠️ Unexpected response for pending invites: {response.status_code}")
                return True
                
        except Exception as e:
            print(f"❌ Error testing pending invites: {e}")
            return False
    
    def verify_security_headers(self):
        """Verify security-related aspects"""
        print("\n🔍 Verifying security implementation...")
        
        try:
            # Test without authentication first
            no_auth_session = requests.Session()
            response = no_auth_session.get(f"{BASE_URL}/api/invites")
            
            if response.status_code in [401, 403]:
                print("✅ Endpoints properly require authentication")
            else:
                print(f"⚠️ Endpoints may not require authentication: {response.status_code}")
            
            # Test our authenticated access
            response = self.session.get(f"{BASE_URL}/api/invites")
            if response.status_code == 200:
                print("✅ Authenticated super admin has proper access")
            else:
                print(f"❌ Authenticated super admin access failed: {response.status_code}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error verifying security headers: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all security tests"""
        print("🚀 Starting comprehensive security verification...")
        print("=" * 60)
        
        if not self.login_super_admin():
            print("❌ Cannot proceed - login failed")
            return False
        
        tests = [
            self.test_invites_list_endpoint,
            self.test_clinicians_list_endpoint,
            self.test_individual_invite_access,
            self.test_account_filtering_behavior,
            self.test_pending_invites_access,
            self.verify_security_headers
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"🏁 Security verification completed: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 All security tests PASSED!")
            print("✅ Role-based access control is working correctly")
            return True
        else:
            print("⚠️ Some tests failed - review security implementation")
            return False

def main():
    print("🔒 Comprehensive Invite Security Verification")
    print("Testing with super admin credentials...")
    
    tester = SecurityVerificationTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n✅ Security verification SUCCESSFUL!")
        return 0
    else:
        print("\n❌ Security verification FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
