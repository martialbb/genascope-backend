#!/usr/bin/env python3
"""
End-to-End test script for Account API endpoints.
Tests all account-related API functionality.
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
ACCOUNTS_API = f"{BASE_URL}/api/accounts"

# Test credentials - found in create_test_users.py script
SUPER_ADMIN_EMAIL = "superadmin@genascope.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin123!"

def get_auth_token(email=SUPER_ADMIN_EMAIL, password=SUPER_ADMIN_PASSWORD):
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

def get_current_user_info(headers):
    """Get current user's information."""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def test_accounts_api_endpoints():
    """Test all account API endpoints comprehensively."""
    print("🧪 Testing Account API Endpoints")
    print("=" * 50)
    
    # Get authentication token
    print("1. Authenticating with genascope/genascope...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate with genascope/genascope")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Check current user role
    print("\n2. Checking current user role...")
    user_info = get_current_user_info(headers)
    if user_info:
        print(f"✅ Current user: {user_info.get('email', 'N/A')}")
        print(f"   Role: {user_info.get('role', 'N/A')}")
        print(f"   ID: {user_info.get('id', 'N/A')}")
    else:
        print("❌ Failed to get user information")
        return False
    
    # Variables to store created resources for cleanup
    created_account_id = None
    
    try:
        # Test 1: Get all accounts
        print("\n3. Testing get all accounts...")
        response = requests.get(f"{ACCOUNTS_API}/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            accounts_list = response.json()
            print(f"   Response: {json.dumps(accounts_list, indent=2)}")
            print(f"✅ Retrieved {len(accounts_list)} accounts")
        else:
            print(f"❌ Get accounts failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 2: Get accounts with pagination and filtering
        print("\n4. Testing get accounts with pagination...")
        response = requests.get(f"{ACCOUNTS_API}/?skip=0&limit=5&name=test", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            filtered_accounts = response.json()
            print(f"✅ Pagination and filtering works: {len(filtered_accounts)} accounts")
        else:
            print(f"❌ Pagination/filtering failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 3: Create new account (if user has super_admin role)
        print("\n5. Testing create new account...")
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        account_data = {
            "name": f"Test Account {timestamp}",
            "domain": f"testaccount{timestamp}.com",
            "admin_email": f"admin.{timestamp}@testaccount.com",
            "admin_name": f"Test Admin {timestamp}",
            "admin_password": "TestPassword123!",
            "admin_confirm_password": "TestPassword123!"
        }
        
        response = requests.post(f"{ACCOUNTS_API}/", json=account_data, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            created_account = response.json()
            print(f"   Response: {json.dumps(created_account, indent=2)}")
            created_account_id = created_account["id"]
            print(f"✅ Account created successfully: {created_account_id}")
            print(f"   Name: {created_account['name']}")
            print(f"   Status: {created_account['status']}")
        elif response.status_code == 403:
            print(f"⚠️ Create account forbidden (insufficient permissions): {response.status_code}")
            print(f"   This is expected if user is not super_admin")
        else:
            print(f"❌ Create account failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 4: Get specific account by ID (if we created one)
        if created_account_id:
            print("\n6. Testing get account by ID...")
            response = requests.get(f"{ACCOUNTS_API}/{created_account_id}", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                account_detail = response.json()
                print(f"   Response: {json.dumps(account_detail, indent=2)}")
                print(f"✅ Retrieved account: {account_detail['id']}")
                print(f"   Name: {account_detail['name']}")
                print(f"   Status: {account_detail['status']}")
            else:
                print(f"❌ Get account by ID failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            # Test with a non-existent ID to check error handling
            print("\n6. Testing get account by ID (non-existent)...")
            response = requests.get(f"{ACCOUNTS_API}/non-existent-id", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 404:
                print("✅ 404 error for non-existent account")
            else:
                print(f"⚠️ Unexpected response for non-existent account: {response.status_code}")
        
        # Test 5: Update account (if we created one)
        if created_account_id:
            print("\n7. Testing update account...")
            update_data = {
                "name": f"Updated Test Account {timestamp}",
                "domain": f"updated-testaccount{timestamp}.com",
                "status": "active"
            }
            
            response = requests.put(f"{ACCOUNTS_API}/{created_account_id}", json=update_data, headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                updated_account = response.json()
                print(f"   Response: {json.dumps(updated_account, indent=2)}")
                print(f"✅ Account updated successfully")
                print(f"   New name: {updated_account['name']}")
                print(f"   Status: {updated_account['status']}")
            else:
                print(f"❌ Update account failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print("\n7. Skipping update test (no account created)")
        
        # Test 6: Error handling tests
        print("\n8. Testing error handling...")
        
        # Test with invalid account data
        invalid_account_data = {
            "name": "",  # Invalid empty name
            "admin_email": "invalid-email",  # Invalid email format
            "admin_password": "123",  # Too short password
            "admin_confirm_password": "different"  # Non-matching password
        }
        
        response = requests.post(f"{ACCOUNTS_API}/", json=invalid_account_data, headers=headers)
        if response.status_code == 422 or response.status_code == 400:
            print("✅ 422/400 error for invalid account data")
        elif response.status_code == 403:
            print("⚠️ 403 error (insufficient permissions)")
        else:
            print(f"⚠️ Unexpected response for invalid data: {response.status_code}")
        
        # Test 7: Delete account (if we created one and user has super_admin role)
        if created_account_id:
            print("\n9. Testing delete account...")
            response = requests.delete(f"{ACCOUNTS_API}/{created_account_id}", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                delete_result = response.json()
                print(f"   Response: {json.dumps(delete_result, indent=2)}")
                print(f"✅ Account deleted successfully")
                created_account_id = None  # Clear for cleanup
            elif response.status_code == 403:
                print(f"⚠️ Delete account forbidden (insufficient permissions): {response.status_code}")
                print(f"   This is expected if user is not super_admin")
            else:
                print(f"❌ Delete account failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print("\n9. Skipping delete test (no account created)")
        
        # Test 8: Test authentication without token
        print("\n10. Testing authentication requirements...")
        response = requests.get(f"{ACCOUNTS_API}/")  # No headers
        if response.status_code == 401:
            print("✅ 401 error when no authentication provided")
        else:
            print(f"⚠️ Unexpected response without auth: {response.status_code}")
        
        # Test 9: Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token-123"}
        response = requests.get(f"{ACCOUNTS_API}/", headers=invalid_headers)
        if response.status_code == 401:
            print("✅ 401 error for invalid token")
        else:
            print(f"⚠️ Unexpected response for invalid token: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("🎉 Accounts API testing completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup - try to delete any created account
        if created_account_id:
            print(f"\n11. Cleaning up created account...")
            try:
                response = requests.delete(f"{ACCOUNTS_API}/{created_account_id}", headers=headers)
                if response.status_code == 200:
                    print(f"✅ Cleanup successful")
                else:
                    print(f"⚠️ Cleanup failed: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")

if __name__ == "__main__":
    success = test_accounts_api_endpoints()
    sys.exit(0 if success else 1)
