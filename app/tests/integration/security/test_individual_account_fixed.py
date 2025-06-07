#!/usr/bin/env python3

import requests
import json

# Test the fixed individual account endpoint
def test_individual_account_endpoint():
    """Test the individual account endpoint that was causing 500 errors"""
    base_url = "http://localhost:8000"
    
    print("🔧 Testing Individual Account Endpoint Fix")
    print("=" * 50)
    
    # Step 1: Login as superadmin to get token
    login_data = {
        "username": "admin@test.com",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/token", data=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Get list of accounts to find an account ID
    try:
        accounts_response = requests.get(f"{base_url}/api/accounts/", headers=headers)
        if accounts_response.status_code != 200:
            print(f"❌ Failed to get accounts list: {accounts_response.status_code}")
            return False
            
        accounts = accounts_response.json()
        if not accounts:
            print("❌ No accounts found")
            return False
            
        first_account = accounts[0]
        account_id = first_account["id"]
        print(f"✅ Found account to test: {first_account['name']} (ID: {account_id})")
        
    except Exception as e:
        print(f"❌ Error getting accounts list: {e}")
        return False
    
    # Step 3: Test individual account endpoint
    try:
        individual_response = requests.get(f"{base_url}/api/accounts/{account_id}", headers=headers)
        
        print(f"\n📋 Individual Account Endpoint Test:")
        print(f"URL: GET /api/accounts/{account_id}")
        print(f"Status Code: {individual_response.status_code}")
        
        if individual_response.status_code == 200:
            account_data = individual_response.json()
            print("✅ SUCCESS: Individual account endpoint working!")
            print(f"Account Details:")
            print(f"  - ID: {account_data.get('id')}")
            print(f"  - Name: {account_data.get('name')}")
            print(f"  - Status: {account_data.get('status')}")
            print(f"  - Created: {account_data.get('created_at', 'N/A')}")
            print(f"  - Updated: {account_data.get('updated_at', 'N/A')}")
            return True
        else:
            print(f"❌ FAILED: Status {individual_response.status_code}")
            print(f"Response: {individual_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing individual account endpoint: {e}")
        return False

# Step 4: Test with multiple accounts
def test_multiple_accounts():
    """Test individual endpoint with multiple accounts"""
    base_url = "http://localhost:8000"
    
    # Login
    login_data = {
        "username": "admin@test.com", 
        "password": "admin123"
    }
    
    login_response = requests.post(f"{base_url}/api/auth/token", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all accounts
    accounts_response = requests.get(f"{base_url}/api/accounts/", headers=headers)
    accounts = accounts_response.json()
    
    print(f"\n🔍 Testing Multiple Individual Account Requests:")
    print("=" * 50)
    
    success_count = 0
    total_count = min(3, len(accounts))  # Test first 3 accounts
    
    for i, account in enumerate(accounts[:3]):
        account_id = account["id"]
        account_name = account["name"]
        
        try:
            response = requests.get(f"{base_url}/api/accounts/{account_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Account {i+1}: {account_name} - SUCCESS")
                print(f"   ID matches: {data['id'] == account_id}")
                print(f"   Name matches: {data['name'] == account_name}")
                success_count += 1
            else:
                print(f"❌ Account {i+1}: {account_name} - FAILED ({response.status_code})")
                
        except Exception as e:
            print(f"❌ Account {i+1}: {account_name} - ERROR: {e}")
    
    print(f"\n📊 Results: {success_count}/{total_count} accounts tested successfully")
    return success_count == total_count

if __name__ == "__main__":
    print("🧪 Testing Individual Account Endpoint Fix")
    print("=" * 60)
    
    # Test the main fix
    main_success = test_individual_account_endpoint()
    
    # Test multiple accounts
    multi_success = test_multiple_accounts()
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"Individual Account Endpoint: {'✅ WORKING' if main_success else '❌ FAILED'}")
    print(f"Multiple Accounts Test: {'✅ WORKING' if multi_success else '❌ FAILED'}")
    
    if main_success and multi_success:
        print(f"\n🎉 ALL TESTS PASSED! Individual account endpoint is now working correctly.")
        print(f"The UUID→string conversion issue has been resolved.")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
