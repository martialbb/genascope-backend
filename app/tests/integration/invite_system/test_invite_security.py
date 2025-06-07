#!/usr/bin/env python3
"""
Comprehensive security test suite for invite endpoints
Tests role-based access control implementation
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USERS = {
    "super_admin": {
        "email": "super_admin@test.com",
        "password": "test123",
        "expected_role": "SUPER_ADMIN"
    },
    "admin_account1": {
        "email": "admin1@test.com", 
        "password": "test123",
        "expected_role": "ADMIN",
        "account_id": "account1"
    },
    "admin_account2": {
        "email": "admin2@test.com",
        "password": "test123", 
        "expected_role": "ADMIN",
        "account_id": "account2"
    },
    "clinician_account1": {
        "email": "clinician1@test.com",
        "password": "test123",
        "expected_role": "CLINICIAN",
        "account_id": "account1"
    }
}

class InviteSecurityTester:
    def __init__(self):
        self.sessions = {}
        self.test_results = []
        
    def login_user(self, user_key: str) -> bool:
        """Login a user and store their session"""
        user_data = TEST_USERS[user_key]
        
        session = requests.Session()
        
        # Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        try:
            response = session.post(f"{BASE_URL}/api/auth/login", data=login_data)
            if response.status_code == 200:
                self.sessions[user_key] = session
                print(f"✅ Successfully logged in {user_key}")
                return True
            else:
                print(f"❌ Failed to login {user_key}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error for {user_key}: {e}")
            return False
    
    def test_invites_list_access(self):
        """Test /api/invites endpoint access control"""
        print("\n🔍 Testing /api/invites endpoint access control...")
        
        for user_key, session in self.sessions.items():
            user_data = TEST_USERS[user_key]
            
            try:
                response = session.get(f"{BASE_URL}/api/invites")
                
                if response.status_code == 200:
                    invites = response.json()
                    print(f"✅ {user_key} can access invites list - Count: {len(invites.get('invites', []))}")
                    
                    # For non-super admins, verify all invites belong to their account
                    if user_data["expected_role"] != "SUPER_ADMIN":
                        account_id = user_data.get("account_id")
                        if account_id:
                            self.verify_account_isolation(invites.get('invites', []), account_id, user_key, "invites list")
                else:
                    print(f"❌ {user_key} cannot access invites list: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error testing invites list for {user_key}: {e}")
    
    def test_clinicians_list_access(self):
        """Test /api/clinicians endpoint access control"""
        print("\n🔍 Testing /api/clinicians endpoint access control...")
        
        for user_key, session in self.sessions.items():
            user_data = TEST_USERS[user_key]
            
            try:
                response = session.get(f"{BASE_URL}/api/clinicians")
                
                if response.status_code == 200:
                    clinicians = response.json()
                    print(f"✅ {user_key} can access clinicians list - Count: {len(clinicians)}")
                    
                    # For non-super admins, verify all clinicians belong to their account
                    if user_data["expected_role"] != "SUPER_ADMIN":
                        account_id = user_data.get("account_id")
                        if account_id:
                            self.verify_clinicians_account_isolation(clinicians, account_id, user_key)
                else:
                    print(f"❌ {user_key} cannot access clinicians list: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error testing clinicians list for {user_key}: {e}")
    
    def test_individual_invite_access(self):
        """Test /api/invites/{invite_id} endpoint access control"""
        print("\n🔍 Testing individual invite access control...")
        
        # First get some invite IDs to test with
        invite_ids = self.get_sample_invite_ids()
        
        if not invite_ids:
            print("⚠️ No invite IDs found for testing individual access")
            return
            
        for user_key, session in self.sessions.items():
            user_data = TEST_USERS[user_key]
            
            for invite_id in invite_ids[:3]:  # Test first 3 invites
                try:
                    response = session.get(f"{BASE_URL}/api/invites/{invite_id}")
                    
                    if response.status_code == 200:
                        invite = response.json()
                        print(f"✅ {user_key} can access invite {invite_id}")
                        
                        # Verify account isolation for non-super admins
                        if user_data["expected_role"] != "SUPER_ADMIN":
                            self.verify_invite_account_access(invite, user_data.get("account_id"), user_key, invite_id)
                            
                    elif response.status_code == 403:
                        print(f"🔒 {user_key} correctly denied access to invite {invite_id}")
                    else:
                        print(f"❌ {user_key} unexpected response for invite {invite_id}: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error testing invite {invite_id} for {user_key}: {e}")
    
    def test_pending_invites_access(self):
        """Test /api/pending/{clinician_id} endpoint access control"""
        print("\n🔍 Testing pending invites access control...")
        
        # Get some clinician IDs to test with
        clinician_ids = self.get_sample_clinician_ids()
        
        if not clinician_ids:
            print("⚠️ No clinician IDs found for testing pending invites")
            return
            
        for user_key, session in self.sessions.items():
            user_data = TEST_USERS[user_key]
            
            for clinician_id in clinician_ids[:2]:  # Test first 2 clinicians
                try:
                    response = session.get(f"{BASE_URL}/api/pending/{clinician_id}")
                    
                    if response.status_code == 200:
                        invites = response.json()
                        print(f"✅ {user_key} can access pending invites for clinician {clinician_id} - Count: {len(invites)}")
                        
                    elif response.status_code == 403:
                        print(f"🔒 {user_key} correctly denied access to pending invites for clinician {clinician_id}")
                    else:
                        print(f"❌ {user_key} unexpected response for pending invites {clinician_id}: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error testing pending invites for {user_key}: {e}")
    
    def get_sample_invite_ids(self) -> List[str]:
        """Get sample invite IDs from super admin session"""
        if "super_admin" not in self.sessions:
            return []
            
        try:
            response = self.sessions["super_admin"].get(f"{BASE_URL}/api/invites")
            if response.status_code == 200:
                invites = response.json()
                return [invite.get("id") for invite in invites.get("invites", []) if invite.get("id")][:5]
        except Exception as e:
            print(f"Error getting sample invite IDs: {e}")
            
        return []
    
    def get_sample_clinician_ids(self) -> List[str]:
        """Get sample clinician IDs from super admin session"""
        if "super_admin" not in self.sessions:
            return []
            
        try:
            response = self.sessions["super_admin"].get(f"{BASE_URL}/api/clinicians")
            if response.status_code == 200:
                clinicians = response.json()
                return [clinician.get("id") for clinician in clinicians if clinician.get("id")][:3]
        except Exception as e:
            print(f"Error getting sample clinician IDs: {e}")
            
        return []
    
    def verify_account_isolation(self, invites: List[Dict], expected_account_id: str, user_key: str, context: str):
        """Verify that all invites belong to the expected account"""
        for invite in invites:
            patient = invite.get("patient", {})
            if patient and patient.get("account_id") != expected_account_id:
                print(f"⚠️ SECURITY ISSUE: {user_key} can see invite for patient from different account in {context}")
                print(f"   Expected account: {expected_account_id}, Found: {patient.get('account_id')}")
    
    def verify_clinicians_account_isolation(self, clinicians: List[Dict], expected_account_id: str, user_key: str):
        """Verify that all clinicians belong to the expected account"""
        for clinician in clinicians:
            if clinician.get("account_id") != expected_account_id:
                print(f"⚠️ SECURITY ISSUE: {user_key} can see clinician from different account")
                print(f"   Expected account: {expected_account_id}, Found: {clinician.get('account_id')}")
    
    def verify_invite_account_access(self, invite: Dict, expected_account_id: str, user_key: str, invite_id: str):
        """Verify that the invite belongs to the expected account"""
        patient = invite.get("patient", {})
        if patient and patient.get("account_id") != expected_account_id:
            print(f"⚠️ SECURITY ISSUE: {user_key} can access invite {invite_id} from different account")
            print(f"   Expected account: {expected_account_id}, Found: {patient.get('account_id')}")
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🚀 Starting comprehensive invite security tests...")
        
        # Login all test users
        print("\n📝 Logging in test users...")
        for user_key in TEST_USERS.keys():
            if not self.login_user(user_key):
                print(f"⚠️ Skipping tests for {user_key} due to login failure")
        
        if not self.sessions:
            print("❌ No users logged in successfully. Cannot proceed with tests.")
            return False
        
        # Run all tests
        self.test_invites_list_access()
        self.test_clinicians_list_access() 
        self.test_individual_invite_access()
        self.test_pending_invites_access()
        
        print("\n✅ All security tests completed!")
        return True

def main():
    print("🔒 Invite Security Test Suite")
    print("=" * 50)
    
    tester = InviteSecurityTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Security testing completed successfully!")
        return 0
    else:
        print("\n❌ Security testing failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
