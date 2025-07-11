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
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImlkIjoiOWJjYjIxOGQtYTk2My00ZWVjLWIxYzUtYmY5MWJiMDQwYWI4Iiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzUxNzYyMDQ4fQ.11-cNUZ39yQyw5LYmG0aKnLElNWSpvJ-K-2kj3O4wqI"

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
    assert health_response.status_code == 200, f"Health check failed: {health_response.status_code}"
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
        assert response.status_code == 200, f"Failed to create {specialty} strategy: {response.status_code} - {response.text}"
        strategy = response.json()
        created_strategies.append(strategy)
        print(f"✅ Created {specialty} strategy: {strategy['id']}")
    
    # Test filtering by each specialty
    print("3. Testing specialty filtering...")
    
    for specialty in specialties:
        print(f"\n   Testing {specialty} filter...")
        response = requests.get(f"{API_BASE}/strategies", headers=headers, params={"specialty": specialty})
        
        assert response.status_code == 200, f"Filter request failed: {response.status_code} - {response.text}"
        filtered_strategies = response.json()
        
        # Find our test strategy for this specialty
        our_strategy = next((s for s in created_strategies if s["specialty"] == specialty), None)
        assert our_strategy is not None, f"Could not find our {specialty} test strategy"
        
        found = any(s["id"] == our_strategy["id"] for s in filtered_strategies)
        assert found, f"{specialty} filter did not return our test strategy"
        print(f"   ✅ {specialty} filter returned our test strategy")
        
        # Verify all returned strategies have the correct specialty
        all_correct = all(s.get("specialty") == specialty for s in filtered_strategies)
        assert all_correct, f"Some strategies have incorrect specialty"
        print(f"   ✅ All {len(filtered_strategies)} strategies have {specialty} specialty")
    
    # Test combined filtering (specialty + active_only)
    print("\n4. Testing combined filters (specialty + active_only)...")
    
    # Activate one strategy
    assert created_strategies, "No strategies created for testing"
    strategy_to_activate = created_strategies[0]
    update_response = requests.put(
        f"{API_BASE}/strategies/{strategy_to_activate['id']}", 
        headers=headers, 
        json={"is_active": True}
    )
    
    assert update_response.status_code == 200, f"Failed to activate strategy: {update_response.status_code}"
    print(f"✅ Activated strategy: {strategy_to_activate['specialty']}")
    
    # Test combined filter
    response = requests.get(
        f"{API_BASE}/strategies", 
        headers=headers, 
        params={"specialty": strategy_to_activate['specialty'], "active_only": True}
    )
    
    assert response.status_code == 200, f"Combined filter request failed: {response.status_code}"
    combined_results = response.json()
    found_our_strategy = any(s["id"] == strategy_to_activate["id"] for s in combined_results)
    
    assert found_our_strategy, "Combined filter did not return our active strategy"
    print(f"✅ Combined filter (specialty + active_only) works correctly")
    
    # Cleanup
    print("\n5. Cleaning up test strategies...")
    for strategy in created_strategies:
        delete_response = requests.delete(f"{API_BASE}/strategies/{strategy['id']}", headers=headers)
        if delete_response.status_code == 200:
            print(f"✅ Deleted strategy: {strategy['id']}")
        else:
            print(f"⚠️ Failed to delete strategy {strategy['id']}: {delete_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 All specialty filtering tests PASSED!")
    # Note: Using assertions instead of return for proper pytest compatibility

if __name__ == "__main__":
    test_specialty_filtering()
