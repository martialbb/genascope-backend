#!/usr/bin/env python3
"""
Test script to verify account access control is working correctly
"""
import requests
import json

def test_account_access():
    base_url = "http://localhost:8000"
    
    print("🔐 Testing Account Access Control")
    print("=" * 60)
    
    # Test 1: Regular Admin should only see their own account
    print("\n1️⃣ Testing Regular Admin Account Access")
    admin_login = requests.post(f"{base_url}/api/auth/token", 
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=admin@test.com&password=admin123"
    )
    
    if admin_login.status_code == 200:
        admin_token = admin_login.json()["access_token"]
        
        # Get accounts as admin
        admin_accounts = requests.get(f"{base_url}/api/accounts/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if admin_accounts.status_code == 200:
            accounts = admin_accounts.json()
            print(f"✅ Regular admin sees {len(accounts)} account(s):")
            for account in accounts:
                print(f"   - {account['name']} (ID: {account['id'][:8]}...)")
            
            if len(accounts) == 1:
                print("✅ CORRECT: Regular admin can only see their own account")
            else:
                print(f"❌ ERROR: Regular admin should only see 1 account, but sees {len(accounts)}")
        else:
            print(f"❌ ERROR: Failed to get accounts as admin: {admin_accounts.status_code}")
    else:
        print(f"❌ ERROR: Admin login failed: {admin_login.status_code}")
    
    # Test 2: Super Admin should see all accounts
    print("\n2️⃣ Testing Super Admin Account Access")
    superadmin_login = requests.post(f"{base_url}/api/auth/token", 
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=superadmin@genascope.com&password=admin123"
    )
    
    if superadmin_login.status_code == 200:
        superadmin_token = superadmin_login.json()["access_token"]
        
        # Get accounts as super admin
        superadmin_accounts = requests.get(f"{base_url}/api/accounts/",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        
        if superadmin_accounts.status_code == 200:
            accounts = superadmin_accounts.json()
            print(f"✅ Super admin sees {len(accounts)} account(s):")
            for account in accounts[:3]:  # Show first 3
                print(f"   - {account['name']} (ID: {account['id'][:8]}...)")
            if len(accounts) > 3:
                print(f"   ... and {len(accounts) - 3} more accounts")
            
            if len(accounts) > 1:
                print("✅ CORRECT: Super admin can see all accounts")
            else:
                print(f"❌ ERROR: Super admin should see multiple accounts, but sees {len(accounts)}")
        else:
            print(f"❌ ERROR: Failed to get accounts as super admin: {superadmin_accounts.status_code}")
    else:
        print(f"❌ ERROR: Super admin login failed: {superadmin_login.status_code}")
    
    print("\n🎯 Account Access Control Test Complete!")

if __name__ == "__main__":
    test_account_access()
