#!/usr/bin/env python3
"""
Test script to verify specialty filtering functionality.
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/chat-configuration"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImlkIjoiZmZlN2QzNTUtZGY1MC00NWE2LTlmYzAtMzhiOWYxYjM0ODZmIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzUxMTYwOTAxfQ.B2ZAy5odCF3sJYJswJzdv-KckgZ7-r_HG9G8StiEb8w"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_specialty_filtering():
    """Test the specialty filtering functionality."""
    print("🧪 Testing Specialty Filtering Functionality")
    print("=" * 50)
    
    # Health check first
    print("1. Health check...")
    health_response = requests.get(f"{API_BASE}/health", headers=headers)
    if health_response.status_code != 200:
        print(f"❌ Health check failed: {health_response.status_code}")
        return False
    print("✅ Health check passed")
    
    # Create test strategies with different specialties
    created_strategies = []
    specialties = ["Oncology", "Cardiology", "Gastroenterology"]
    
    print("2. Creating test strategies...")
    for specialty in specialties:
        strategy_data = {
            "name": f"Test {specialty} Strategy {datetime.now().strftime('%H%M%S')}",
            "description": f"Testing {specialty} specialty filtering",
            "goal": f"Test {specialty} goals",
            "patient_introduction": f"Welcome to {specialty} assessment",
            "specialty": specialty,
            "knowledge_source_ids": [],
            "targeting_rules": [],
            "outcome_actions": []
        }
        
        response = requests.post(f"{API_BASE}/strategies", headers=headers, json=strategy_data)
        if response.status_code == 200:
            strategy = response.json()
            created_strategies.append(strategy)
            print(f"✅ Created {specialty} strategy: {strategy['id']}")
        else:
            print(f"❌ Failed to create {specialty} strategy: {response.status_code} - {response.text}")
            return False
    
    # Test filtering by each specialty
    print("3. Testing specialty filtering...")
    success = True
    
    for specialty in specialties:
        print(f"\n   Testing {specialty} filter...")
        response = requests.get(f"{API_BASE}/strategies", headers=headers, params={"specialty": specialty})
        
        if response.status_code == 200:
            filtered_strategies = response.json()
            
            # Find our test strategy for this specialty
            our_strategy = next((s for s in created_strategies if s["specialty"] == specialty), None)
            if our_strategy:
                found = any(s["id"] == our_strategy["id"] for s in filtered_strategies)
                if found:
                    print(f"   ✅ {specialty} filter returned our test strategy")
                    
                    # Verify all returned strategies have the correct specialty
                    all_correct = all(s.get("specialty") == specialty for s in filtered_strategies)
                    if all_correct:
                        print(f"   ✅ All {len(filtered_strategies)} strategies have {specialty} specialty")
                    else:
                        print(f"   ❌ Some strategies have incorrect specialty")
                        success = False
                else:
                    print(f"   ❌ {specialty} filter did not return our test strategy")
                    success = False
            else:
                print(f"   ❌ Could not find our {specialty} test strategy")
                success = False
        else:
            print(f"   ❌ Filter request failed: {response.status_code} - {response.text}")
            success = False
    
    # Test combined filtering (specialty + active_only)
    print("\n4. Testing combined filters (specialty + active_only)...")
    
    # Activate one strategy
    if created_strategies:
        strategy_to_activate = created_strategies[0]
        update_response = requests.put(
            f"{API_BASE}/strategies/{strategy_to_activate['id']}", 
            headers=headers, 
            json={"is_active": True}
        )
        
        if update_response.status_code == 200:
            print(f"✅ Activated strategy: {strategy_to_activate['specialty']}")
            
            # Test combined filter
            response = requests.get(
                f"{API_BASE}/strategies", 
                headers=headers, 
                params={"specialty": strategy_to_activate['specialty'], "active_only": True}
            )
            
            if response.status_code == 200:
                combined_results = response.json()
                found_our_strategy = any(s["id"] == strategy_to_activate["id"] for s in combined_results)
                
                if found_our_strategy:
                    print(f"✅ Combined filter (specialty + active_only) works correctly")
                else:
                    print(f"❌ Combined filter did not return our active strategy")
                    success = False
            else:
                print(f"❌ Combined filter request failed: {response.status_code}")
                success = False
        else:
            print(f"❌ Failed to activate strategy: {update_response.status_code}")
            success = False
    
    # Cleanup
    print("\n5. Cleaning up test strategies...")
    for strategy in created_strategies:
        delete_response = requests.delete(f"{API_BASE}/strategies/{strategy['id']}", headers=headers)
        if delete_response.status_code == 200:
            print(f"✅ Deleted strategy: {strategy['id']}")
        else:
            print(f"⚠️ Failed to delete strategy {strategy['id']}: {delete_response.status_code}")
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All specialty filtering tests PASSED!")
        return True
    else:
        print("❌ Some specialty filtering tests FAILED!")
        return False

if __name__ == "__main__":
    test_specialty_filtering()
