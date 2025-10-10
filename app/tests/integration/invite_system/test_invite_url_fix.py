#!/usr/bin/env python3
"""
Quick test to verify invite URL generation after updating FRONTEND_URL
"""
import requests
import os
import sys

def test_invite_url_generation():
    """Test that invite URLs are now using the correct domain"""
    
    # Check if we can access the backend
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print("❌ Backend health check failed")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Check environment variables in the pod
    print("\n🔍 Checking environment variables...")
    import subprocess
    try:
        result = subprocess.run([
            "kubectl", "exec", "-it", 
            "genascope-backend-56cb5979d8-mhm57",
            "--namespace", "dev", "--",
            "env"
        ], capture_output=True, text=True)
        
        env_lines = result.stdout.split('\n')
        frontend_url = None
        for line in env_lines:
            if line.startswith('FRONTEND_URL='):
                frontend_url = line.split('=', 1)[1]
                break
        
        if frontend_url:
            print(f"✅ FRONTEND_URL is set to: {frontend_url}")
            if 'chat-dev.genascope.com' in frontend_url:
                print("✅ Frontend URL is correctly configured with external domain")
                return True
            else:
                print("❌ Frontend URL still uses localhost")
                return False
        else:
            print("❌ FRONTEND_URL environment variable not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking environment variables: {e}")
        return False

if __name__ == "__main__":
    success = test_invite_url_generation()
    sys.exit(0 if success else 1)
