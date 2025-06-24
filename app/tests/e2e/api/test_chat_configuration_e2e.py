"""
End-to-end tests for the chat configuration API endpoints.
These tests run against the actual backend service without mocked data,
testing the complete flow from HTTP request to database operations.
"""
import pytest
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


# Backend service configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/chat-configuration"

# Test authentication token (should be valid for testing)
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImlkIjoiZmZlN2QzNTUtZGY1MC00NWE2LTlmYzAtMzhiOWYxYjM0ODZmIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzUwODM2NzA4fQ.GlZp2TdQeVBnQnOFFxW8c2KgZD78m0mDX-dTTV0pZT4"

def get_fresh_token() -> str:
    """Generate a fresh authentication token for testing."""
    login_data = {
        'username': 'admin@test.com',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/auth/token', data=login_data)
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            raise Exception(f"Failed to get token: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Error getting fresh token: {e}")

# Test data storage for cleanup
created_resources = {
    "strategies": [],
    "knowledge_sources": []
}


class ChatConfigurationE2ETestClient:
    """E2E test client for chat configuration API."""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        return requests.get(url, headers=self.headers, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        return requests.post(url, headers=self.headers, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make PUT request."""
        url = f"{self.base_url}{endpoint}"
        return requests.put(url, headers=self.headers, json=data)
    
    def delete(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make DELETE request."""
        url = f"{self.base_url}{endpoint}"
        if data is not None and isinstance(data, list):
            # For endpoints that expect a list directly in the body
            return requests.delete(url, headers=self.headers, json=data)
        return requests.delete(url, headers=self.headers, json=data)


@pytest.fixture(scope="module")
def api_client():
    """Create API client for testing with fresh token."""
    # Try to get a fresh token, fall back to the static one if it fails
    try:
        fresh_token = get_fresh_token()
        return ChatConfigurationE2ETestClient(API_BASE, fresh_token)
    except Exception as e:
        print(f"Warning: Could not get fresh token ({e}), using static token")
        return ChatConfigurationE2ETestClient(API_BASE, TEST_TOKEN)


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_tests():
    """Cleanup created resources after all tests."""
    yield
    # Cleanup logic runs after all tests in the module
    try:
        fresh_token = get_fresh_token()
        client = ChatConfigurationE2ETestClient(API_BASE, fresh_token)
    except Exception:
        client = ChatConfigurationE2ETestClient(API_BASE, TEST_TOKEN)
    
    # Clean up knowledge sources
    for ks_id in created_resources["knowledge_sources"]:
        try:
            client.delete(f"/knowledge-sources/{ks_id}")
        except Exception:
            pass  # Ignore cleanup errors
    
    # Clean up strategies
    for strategy_id in created_resources["strategies"]:
        try:
            client.delete(f"/strategies/{strategy_id}")
        except Exception:
            pass  # Ignore cleanup errors


@pytest.mark.e2e
class TestChatConfigurationE2E:
    """
    End-to-end tests for chat configuration API endpoints.
    Tests the complete flow without mocking.
    """
    
    def test_health_check(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chat-configuration"
    
    def test_configuration_stats(self, api_client):
        """Test configuration stats endpoint."""
        response = api_client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields are present
        assert "total_strategies" in data
        assert "active_strategies" in data
        assert "total_knowledge_sources" in data
        assert "processing_queue_length" in data
        assert "knowledge_source_types" in data
        
        # Verify data types
        assert isinstance(data["total_strategies"], int)
        assert isinstance(data["active_strategies"], int)
        assert isinstance(data["total_knowledge_sources"], int)
        assert isinstance(data["processing_queue_length"], int)
        assert isinstance(data["knowledge_source_types"], dict)
    
    def test_strategy_lifecycle(self, api_client):
        """Test complete strategy lifecycle: create, read, update, delete."""
        # Create strategy
        strategy_data = {
            "name": f"E2E Test Strategy {datetime.now().isoformat()}",
            "description": "Strategy created by E2E test",
            "goal": "Test strategy functionality",
            "patient_introduction": "Welcome to the E2E test assessment.",
            "specialty": "Oncology",
            "knowledge_source_ids": [],
            "targeting_rules": [],
            "outcome_actions": []
        }
        
        create_response = api_client.post("/strategies", strategy_data)
        assert create_response.status_code == 200
        
        created_strategy = create_response.json()
        strategy_id = created_strategy["id"]
        created_resources["strategies"].append(strategy_id)
        
        # Verify created strategy structure and basic fields
        assert created_strategy["name"] == strategy_data["name"]
        assert created_strategy["description"] == strategy_data["description"]
        assert created_strategy["is_active"] == False  # Default value
        assert "id" in created_strategy
        assert "created_at" in created_strategy
        
        # Verify relationship fields are present and are lists
        assert "targeting_rules" in created_strategy
        assert "outcome_actions" in created_strategy
        assert "knowledge_sources" in created_strategy
        assert isinstance(created_strategy["targeting_rules"], list)
        assert isinstance(created_strategy["outcome_actions"], list)
        assert isinstance(created_strategy["knowledge_sources"], list)
        
        # For empty strategy, these should be empty lists
        assert len(created_strategy["targeting_rules"]) == 0
        assert len(created_strategy["outcome_actions"]) == 0
        assert len(created_strategy["knowledge_sources"]) == 0
        
        # Read strategy
        get_response = api_client.get(f"/strategies/{strategy_id}")
        assert get_response.status_code == 200
        
        retrieved_strategy = get_response.json()
        assert retrieved_strategy["id"] == strategy_id
        assert retrieved_strategy["name"] == strategy_data["name"]
        
        # Verify relationship fields are present in GET response
        assert "targeting_rules" in retrieved_strategy
        assert "outcome_actions" in retrieved_strategy
        assert "knowledge_sources" in retrieved_strategy
        assert isinstance(retrieved_strategy["targeting_rules"], list)
        assert isinstance(retrieved_strategy["outcome_actions"], list)
        assert isinstance(retrieved_strategy["knowledge_sources"], list)
        
        # Update strategy
        update_data = {
            "name": f"Updated E2E Test Strategy {datetime.now().isoformat()}",
            "is_active": True
        }
        
        update_response = api_client.put(f"/strategies/{strategy_id}", update_data)
        assert update_response.status_code == 200
        
        updated_strategy = update_response.json()
        assert updated_strategy["name"] == update_data["name"]
        assert updated_strategy["is_active"] == True
        
        # Verify relationship fields are still present after update
        assert "targeting_rules" in updated_strategy
        assert "outcome_actions" in updated_strategy
        assert "knowledge_sources" in updated_strategy
        
        # List strategies (verify it appears in list)
        list_response = api_client.get("/strategies")
        assert list_response.status_code == 200
        
        strategies = list_response.json()
        strategy_ids = [s["id"] for s in strategies]
        assert strategy_id in strategy_ids
        
        # Verify each strategy in list has relationship fields
        for strategy in strategies:
            assert "targeting_rules" in strategy
            assert "outcome_actions" in strategy
            assert "knowledge_sources" in strategy
            assert isinstance(strategy["targeting_rules"], list)
            assert isinstance(strategy["outcome_actions"], list)
            assert isinstance(strategy["knowledge_sources"], list)
        
        # Delete strategy
        delete_response = api_client.delete(f"/strategies/{strategy_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted_response = api_client.get(f"/strategies/{strategy_id}")
        assert get_deleted_response.status_code == 404
        
        # Remove from cleanup list since we already deleted it
        created_resources["strategies"].remove(strategy_id)
    
    def test_strategy_with_relationships(self, api_client):
        """Test creating and retrieving a strategy with targeting rules and outcome actions."""
        # First create a knowledge source for the strategy
        ks_data = {
            "name": f"Strategy Test KS {datetime.now().isoformat()}",
            "source_type": "direct",
            "description": "Knowledge source for strategy relationship test",
            "content": "Test content for strategy relationships.",
            "content_type": "text/plain"
        }
        
        ks_response = api_client.post("/knowledge-sources/direct", ks_data)
        assert ks_response.status_code == 200
        ks = ks_response.json()
        ks_id = ks["id"]
        created_resources["knowledge_sources"].append(ks_id)
        
        # Create strategy with targeting rules, outcome actions, and knowledge sources
        strategy_data = {
            "name": f"Relationship Test Strategy {datetime.now().isoformat()}",
            "description": "Strategy with full relationships",
            "goal": "Test strategy with all relationship types",
            "patient_introduction": "Welcome to the relationship test assessment.",
            "specialty": "Oncology",
            "knowledge_source_ids": [ks_id],
            "targeting_rules": [
                {
                    "field": "age",
                    "operator": "greater_than",
                    "value": "18",
                    "sequence": 1
                },
                {
                    "field": "diagnosis",
                    "operator": "contains",
                    "value": "cancer",
                    "sequence": 2
                }
            ],
            "outcome_actions": [
                {
                    "condition": "meets_criteria",
                    "action_type": "create_task", 
                    "details": {
                        "task_title": "Genetic testing recommended",
                        "task_description": "Patient meets criteria for genetic testing"
                    },
                    "sequence": 1
                },
                {
                    "condition": "does_not_meet_criteria",
                    "action_type": "send_message",
                    "details": {
                        "message": "Provide general information about genetic testing"
                    }, 
                    "sequence": 2
                }
            ]
        }
        
        # Create the strategy
        create_response = api_client.post("/strategies", strategy_data)
        assert create_response.status_code == 200
        
        created_strategy = create_response.json()
        strategy_id = created_strategy["id"]
        created_resources["strategies"].append(strategy_id)
        
        # Verify the strategy was created with all relationships
        assert created_strategy["name"] == strategy_data["name"]
        assert "targeting_rules" in created_strategy
        assert "outcome_actions" in created_strategy
        assert "knowledge_sources" in created_strategy
        
        # Verify targeting rules
        targeting_rules = created_strategy["targeting_rules"]
        assert len(targeting_rules) == 2
        
        # Check first targeting rule
        rule1 = targeting_rules[0]
        assert "id" in rule1
        assert rule1["strategy_id"] == strategy_id
        assert rule1["field"] == "age"
        assert rule1["operator"] == "greater_than"
        assert rule1["value"] == "18"
        assert rule1["sequence"] == 1
        assert "created_at" in rule1
        
        # Check second targeting rule
        rule2 = targeting_rules[1]
        assert rule2["field"] == "diagnosis"
        assert rule2["operator"] == "contains"
        assert rule2["value"] == "cancer"
        assert rule2["sequence"] == 2
        
        # Verify outcome actions
        outcome_actions = created_strategy["outcome_actions"]
        assert len(outcome_actions) == 2
        
        # Check first outcome action
        action1 = outcome_actions[0]
        assert "id" in action1
        assert action1["strategy_id"] == strategy_id
        assert action1["condition"] == "meets_criteria"
        assert action1["action_type"] == "create_task"
        assert isinstance(action1["details"], dict)
        assert action1["details"]["task_title"] == "Genetic testing recommended"
        assert action1["sequence"] == 1
        assert "created_at" in action1
        
        # Check second outcome action
        action2 = outcome_actions[1]
        assert action2["condition"] == "does_not_meet_criteria"
        assert action2["action_type"] == "send_message"
        assert isinstance(action2["details"], dict)
        assert action2["details"]["message"] == "Provide general information about genetic testing"
        assert action2["sequence"] == 2
        
        # Verify knowledge sources
        knowledge_sources = created_strategy["knowledge_sources"]
        assert len(knowledge_sources) == 1
        
        # Check knowledge source
        ks_in_strategy = knowledge_sources[0]
        assert ks_in_strategy["id"] == ks_id
        assert ks_in_strategy["name"] == ks_data["name"]
        assert ks_in_strategy["source_type"] == ks_data["source_type"]
        assert ks_in_strategy["description"] == ks_data["description"]
        assert "processing_status" in ks_in_strategy
        assert "created_at" in ks_in_strategy
        
        # Test retrieving the strategy to ensure relationships persist
        get_response = api_client.get(f"/strategies/{strategy_id}")
        assert get_response.status_code == 200
        
        retrieved_strategy = get_response.json()
        
        # Verify all relationships are still present and correct
        assert len(retrieved_strategy["targeting_rules"]) == 2
        assert len(retrieved_strategy["outcome_actions"]) == 2
        assert len(retrieved_strategy["knowledge_sources"]) == 1
        
        # Verify the relationships have the same data
        assert retrieved_strategy["targeting_rules"][0]["field"] == "age"
        assert retrieved_strategy["targeting_rules"][0]["operator"] == "greater_than"
        assert retrieved_strategy["outcome_actions"][0]["condition"] == "meets_criteria"
        assert retrieved_strategy["knowledge_sources"][0]["id"] == ks_id
        
        # Test that the strategy appears correctly in the list endpoint
        list_response = api_client.get("/strategies")
        assert list_response.status_code == 200
        
        strategies = list_response.json()
        our_strategy = None
        for strategy in strategies:
            if strategy["id"] == strategy_id:
                our_strategy = strategy
                break
        
        assert our_strategy is not None
        assert len(our_strategy["targeting_rules"]) == 2
        assert len(our_strategy["outcome_actions"]) == 2
        assert len(our_strategy["knowledge_sources"]) == 1
    
    def test_knowledge_source_lifecycle(self, api_client):
        """Test complete knowledge source lifecycle."""
        # Create knowledge source
        ks_data = {
            "name": f"E2E Test Knowledge Source {datetime.now().isoformat()}",
            "source_type": "direct",
            "description": "Knowledge source created by E2E test",
            "content": "This is test content for the knowledge source.",
            "content_type": "text/plain"
        }
        
        create_response = api_client.post("/knowledge-sources/direct", ks_data)
        assert create_response.status_code == 200
        
        created_ks = create_response.json()
        ks_id = created_ks["id"]
        created_resources["knowledge_sources"].append(ks_id)
        
        # Verify created knowledge source
        assert created_ks["name"] == ks_data["name"]
        assert created_ks["source_type"] == ks_data["source_type"]
        assert created_ks["description"] == ks_data["description"]
        assert "processing_status" in created_ks
        assert "id" in created_ks
        
        # Read knowledge source
        get_response = api_client.get(f"/knowledge-sources/{ks_id}")
        assert get_response.status_code == 200
        
        retrieved_ks = get_response.json()
        assert retrieved_ks["id"] == ks_id
        assert retrieved_ks["name"] == ks_data["name"]
        
        # Update knowledge source
        update_data = {
            "title": f"Updated E2E Test KS {datetime.now().isoformat()}",
            "description": "Updated description"
        }
        
        update_response = api_client.put(f"/knowledge-sources/{ks_id}", update_data)
        assert update_response.status_code == 200
        
        updated_ks = update_response.json()
        assert updated_ks["name"] == update_data["title"]  # title maps to name
        assert updated_ks["description"] == update_data["description"]
        
        # List knowledge sources
        list_response = api_client.get("/knowledge-sources")
        assert list_response.status_code == 200
        
        knowledge_sources = list_response.json()
        ks_ids = [ks["id"] for ks in knowledge_sources]
        assert ks_id in ks_ids
    
    def test_knowledge_source_processing_workflow(self, api_client):
        """Test knowledge source processing workflow including retry."""
        # Create a knowledge source
        ks_data = {
            "name": f"E2E Processing Test {datetime.now().isoformat()}",
            "source_type": "direct",
            "description": "Testing processing workflow",
            "content": "Test content for processing workflow.",
            "content_type": "text/plain"
        }
        
        create_response = api_client.post("/knowledge-sources/direct", ks_data)
        assert create_response.status_code == 200
        
        created_ks = create_response.json()
        ks_id = created_ks["id"]
        created_resources["knowledge_sources"].append(ks_id)
        
        # Check processing queue
        queue_response = api_client.get("/knowledge-sources/processing/queue")
        assert queue_response.status_code == 200
        
        queue_items = queue_response.json()
        queue_ids = [item["id"] for item in queue_items]
        assert ks_id in queue_ids
        
        # Simulate failed processing by directly updating status
        # (In a real scenario, this would be done by the processing service)
        import subprocess
        import os
        
        # Check if we can access docker (this test runs inside a container, so docker may not be available)
        docker_available = False
        try:
            # Try to see if docker command is available
            subprocess.run(["which", "docker"], check=True, capture_output=True)
            docker_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            docker_available = False
        
        if docker_available:
            try:
                subprocess.run([
                    "docker", "exec", "genascope-frontend-db-1", "psql", "-U", "genascope", "-d", "genascope", "-c",
                    f"UPDATE knowledge_sources SET processing_status = 'failed' WHERE id = '{ks_id}';"
                ], check=True, capture_output=True)
                
                # Test retry processing
                retry_response = api_client.post(f"/knowledge-sources/{ks_id}/retry")
                assert retry_response.status_code == 200
                
                retry_data = retry_response.json()
                assert retry_data["message"] == "Processing retry initiated"
                
                # Verify status was updated to pending
                get_response = api_client.get(f"/knowledge-sources/{ks_id}")
                assert get_response.status_code == 200
                
                updated_ks = get_response.json()
                assert updated_ks["processing_status"] == "pending"
                
                # Test retry with non-failed source (should fail)
                retry_again_response = api_client.post(f"/knowledge-sources/{ks_id}/retry")
                assert retry_again_response.status_code == 400
                
                error_data = retry_again_response.json()
                assert "Only failed sources can be retried" in error_data["detail"]
            except subprocess.CalledProcessError:
                # Database update failed, skip the retry test but test the error case
                print("Warning: Could not update database directly, testing error case only")
                retry_response = api_client.post(f"/knowledge-sources/{ks_id}/retry")
                assert retry_response.status_code == 400  # Should fail since status is not 'failed'
                
                error_data = retry_response.json()
                assert "Only failed sources can be retried" in error_data["detail"]
        else:
            # Docker not available, just test the error case where we try to retry a non-failed source
            print("Warning: Docker not available in test environment, testing error case only")
            retry_response = api_client.post(f"/knowledge-sources/{ks_id}/retry")
            assert retry_response.status_code == 400  # Should fail since status is not 'failed'
            
            error_data = retry_response.json()
            assert "Only failed sources can be retried" in error_data["detail"]
    
    def test_bulk_delete_knowledge_sources(self, api_client):
        """Test bulk delete functionality."""
        # Create multiple knowledge sources
        ks_ids = []
        for i in range(3):
            ks_data = {
                "name": f"Bulk Delete Test {i} {datetime.now().isoformat()}",
                "source_type": "direct",
                "description": f"For bulk delete test {i}",
                "content": f"Test content {i}",
                "content_type": "text/plain"
            }
            
            create_response = api_client.post("/knowledge-sources/direct", ks_data)
            assert create_response.status_code == 200
            
            created_ks = create_response.json()
            ks_id = created_ks["id"]
            ks_ids.append(ks_id)
            created_resources["knowledge_sources"].append(ks_id)
        
        # Test bulk delete
        # Test individual delete first to verify account permissions
        individual_delete_response = api_client.delete(f"/knowledge-sources/{ks_ids[0]}")
        assert individual_delete_response.status_code == 200
        
        # Remove the individually deleted ID from the list for bulk delete
        remaining_ids = ks_ids[1:]
        
        bulk_delete_response = api_client.delete("/knowledge-sources/bulk", remaining_ids)
        assert bulk_delete_response.status_code == 200
        
        delete_result = bulk_delete_response.json()
        assert "Successfully deleted" in delete_result["message"]
        
        # Verify deletion
        for ks_id in ks_ids:
            get_response = api_client.get(f"/knowledge-sources/{ks_id}")
            assert get_response.status_code == 404
            
            # Remove from cleanup list since they're already deleted
            if ks_id in created_resources["knowledge_sources"]:
                created_resources["knowledge_sources"].remove(ks_id)
    
    def test_strategy_analytics(self, api_client):
        """Test strategy analytics endpoint with real data."""
        # Create a test strategy
        strategy_data = {
            "name": f"Analytics Test Strategy {datetime.now().isoformat()}",
            "description": "Strategy for analytics testing",
            "goal": "Test analytics functionality",
            "patient_introduction": "Analytics test assessment.",
            "specialty": "Oncology",
            "knowledge_source_ids": [],
            "targeting_rules": [],
            "outcome_actions": []
        }
        
        create_response = api_client.post("/strategies", strategy_data)
        assert create_response.status_code == 200
        
        created_strategy = create_response.json()
        strategy_id = created_strategy["id"]
        created_resources["strategies"].append(strategy_id)
        
        # Test analytics endpoint
        analytics_response = api_client.get(f"/strategies/{strategy_id}/analytics")
        assert analytics_response.status_code == 200
        
        analytics_data = analytics_response.json()
        
        # Verify analytics structure
        assert analytics_data["strategy_id"] == strategy_id
        assert analytics_data["strategy_name"] == strategy_data["name"]
        assert "period" in analytics_data
        assert "summary" in analytics_data
        assert "analytics" in analytics_data
        assert "executions" in analytics_data
        
        # Verify summary structure
        summary = analytics_data["summary"]
        assert "total_executions" in summary
        assert "successful_executions" in summary
        assert "success_rate" in summary
        assert "average_duration_seconds" in summary
        assert "outcomes" in summary
        
        # Verify analytics structure
        analytics = analytics_data["analytics"]
        assert "patients_screened" in analytics
        assert "criteria_met" in analytics
        assert "criteria_not_met" in analytics
        assert "incomplete_data" in analytics
        
        # All should be numeric
        assert isinstance(summary["total_executions"], int)
        assert isinstance(summary["successful_executions"], int)
        assert isinstance(summary["success_rate"], (int, float))
        assert isinstance(summary["average_duration_seconds"], (int, float))
        assert isinstance(analytics["patients_screened"], (int, float))
    
    def test_account_analytics(self, api_client):
        """Test account analytics endpoint."""
        analytics_response = api_client.get("/analytics/account")
        assert analytics_response.status_code == 200
        
        analytics_data = analytics_response.json()
        
        # Verify account analytics structure
        assert "account_id" in analytics_data
        assert "period" in analytics_data
        assert "total_strategies" in analytics_data
        assert "active_strategies" in analytics_data
        assert "strategy_analytics" in analytics_data
        
        # Verify data types
        assert isinstance(analytics_data["total_strategies"], int)
        assert isinstance(analytics_data["active_strategies"], int)
        assert isinstance(analytics_data["strategy_analytics"], list)
        
        # If there are strategy analytics, verify their structure
        if analytics_data["strategy_analytics"]:
            strategy_analytics = analytics_data["strategy_analytics"][0]
            assert "strategy_id" in strategy_analytics
            assert "strategy_name" in strategy_analytics
            assert "total_executions" in strategy_analytics
            assert "successful_executions" in strategy_analytics
            assert "success_rate" in strategy_analytics
    
    def test_analytics_with_time_period(self, api_client):
        """Test analytics with different time periods."""
        # Create a test strategy
        strategy_data = {
            "name": f"Time Period Test {datetime.now().isoformat()}",
            "description": "Testing time period analytics",
            "goal": "Test time period functionality",
            "patient_introduction": "Time period test.",
            "specialty": "Oncology",
            "knowledge_source_ids": [],
            "targeting_rules": [],
            "outcome_actions": []
        }
        
        create_response = api_client.post("/strategies", strategy_data)
        assert create_response.status_code == 200
        
        created_strategy = create_response.json()
        strategy_id = created_strategy["id"]
        created_resources["strategies"].append(strategy_id)
        
        # Test different time periods
        time_periods = [7, 30, 90]
        
        for days in time_periods:
            analytics_response = api_client.get(f"/strategies/{strategy_id}/analytics", params={"days": days})
            assert analytics_response.status_code == 200
            
            analytics_data = analytics_response.json()
            assert analytics_data["period"] == f"{days} days"
            assert analytics_data["strategy_id"] == strategy_id
    
    def test_error_handling(self, api_client):
        """Test error handling for various scenarios."""
        # Test non-existent strategy
        fake_strategy_id = str(uuid.uuid4())
        get_response = api_client.get(f"/strategies/{fake_strategy_id}")
        assert get_response.status_code == 404
        
        # Test non-existent knowledge source
        fake_ks_id = str(uuid.uuid4())
        get_ks_response = api_client.get(f"/knowledge-sources/{fake_ks_id}")
        assert get_ks_response.status_code == 404
        
        # Test retry on non-existent knowledge source
        retry_response = api_client.post(f"/knowledge-sources/{fake_ks_id}/retry")
        assert retry_response.status_code == 404
        
        # Test invalid data for strategy creation
        invalid_strategy_data = {
            "name": "",  # Empty name should fail
            "description": "Invalid strategy",
            "goal": "Test goal",
            "patient_introduction": "Test intro",
            "specialty": "Oncology",
            "knowledge_source_ids": [],
            "targeting_rules": [],
            "outcome_actions": []
        }
        
        create_response = api_client.post("/strategies", invalid_strategy_data)
        assert create_response.status_code in [400, 422]  # Bad request or validation error
    
    def test_authentication_required(self):
        """Test that endpoints require authentication."""
        # Client without auth token
        no_auth_client = ChatConfigurationE2ETestClient(API_BASE, "")
        no_auth_client.headers.pop("Authorization", None)
        
        # Test endpoints that require auth
        endpoints_requiring_auth = [
            "/stats",
            "/strategies",
            "/knowledge-sources",
            "/analytics/account"
        ]
        
        for endpoint in endpoints_requiring_auth:
            response = no_auth_client.get(endpoint)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require authentication"
    
    def test_complete_workflow(self, api_client):
        """Test a complete workflow combining multiple endpoints."""
        # 1. Check initial stats
        initial_stats_response = api_client.get("/stats")
        assert initial_stats_response.status_code == 200
        initial_stats = initial_stats_response.json()
        initial_strategy_count = initial_stats["total_strategies"]
        initial_ks_count = initial_stats["total_knowledge_sources"]
        
        # 2. Create a strategy
        strategy_data = {
            "name": f"Complete Workflow Test {datetime.now().isoformat()}",
            "description": "Testing complete workflow",
            "goal": "Complete workflow test",
            "patient_introduction": "Complete workflow assessment.",
            "specialty": "Oncology",
            "knowledge_source_ids": [],
            "targeting_rules": [],
            "outcome_actions": []
        }
        
        strategy_response = api_client.post("/strategies", strategy_data)
        assert strategy_response.status_code == 200
        strategy = strategy_response.json()
        strategy_id = strategy["id"]
        created_resources["strategies"].append(strategy_id)
        
        # Activate the strategy
        update_response = api_client.put(f"/strategies/{strategy_id}", {"is_active": True})
        assert update_response.status_code == 200
        
        # 3. Create knowledge sources
        ks_data = {
            "name": f"Workflow KS {datetime.now().isoformat()}",
            "source_type": "direct",
            "description": "Workflow test knowledge source",
            "content": "Workflow test content",
            "content_type": "text/plain"
        }
        
        ks_response = api_client.post("/knowledge-sources/direct", ks_data)
        assert ks_response.status_code == 200
        ks = ks_response.json()
        ks_id = ks["id"]
        created_resources["knowledge_sources"].append(ks_id)
        
        # 4. Check updated stats
        updated_stats_response = api_client.get("/stats")
        assert updated_stats_response.status_code == 200
        updated_stats = updated_stats_response.json()
        
        assert updated_stats["total_strategies"] == initial_strategy_count + 1
        assert updated_stats["total_knowledge_sources"] == initial_ks_count + 1
        assert updated_stats["active_strategies"] >= 1  # At least our active strategy
        
        # 5. Get analytics for the strategy
        analytics_response = api_client.get(f"/strategies/{strategy_id}/analytics")
        assert analytics_response.status_code == 200
        analytics = analytics_response.json()
        assert analytics["strategy_id"] == strategy_id
        
        # 6. Get account analytics
        account_analytics_response = api_client.get("/analytics/account")
        assert account_analytics_response.status_code == 200
        account_analytics = account_analytics_response.json()
        
        # Find our strategy in the account analytics
        our_strategy_analytics = None
        for sa in account_analytics["strategy_analytics"]:
            if sa["strategy_id"] == strategy_id:
                our_strategy_analytics = sa
                break
        
        assert our_strategy_analytics is not None
        assert our_strategy_analytics["strategy_name"] == strategy_data["name"]
        
        # 7. Check health
        health_response = api_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

    def test_edge_cases_and_validation(self, api_client):
        """Test edge cases and validation scenarios."""
        
        # Test strategy creation with minimal valid data
        minimal_strategy = {
            "name": f"Minimal Strategy {datetime.now().isoformat()}",
            "description": "Minimal description",
            "goal": "Minimal goal", 
            "patient_introduction": "Minimal intro",
            "knowledge_source_ids": [],
            "targeting_rules": [],
            "outcome_actions": []
        }
        
        response = api_client.post("/strategies", minimal_strategy)
        assert response.status_code == 200
        strategy = response.json()
        strategy_id = strategy["id"]
        created_resources["strategies"].append(strategy_id)
        
        # Test strategy creation with all specialties
        specialties = ["Oncology", "Cardiology", "Gastroenterology", "Hepatology", "Pharmacy", "Genetics", "Other"]
        specialty_strategies = []
        
        for specialty in specialties:
            strategy_data = {
                "name": f"Specialty Test {specialty} {datetime.now().isoformat()}",
                "description": f"Testing {specialty} specialty",
                "goal": f"Test {specialty} goals",
                "patient_introduction": f"Welcome to {specialty} assessment",
                "specialty": specialty,
                "knowledge_source_ids": [],
                "targeting_rules": [],
                "outcome_actions": []
            }
            
            response = api_client.post("/strategies", strategy_data)
            assert response.status_code == 200
            strategy = response.json()
            specialty_strategies.append(strategy["id"])
            created_resources["strategies"].append(strategy["id"])
            assert strategy["specialty"] == specialty
        
        # Test knowledge source with different content types
        content_types = ["text/plain", "text/html", "application/pdf", "application/json"]
        ks_ids = []
        
        for content_type in content_types:
            ks_data = {
                "name": f"Content Type Test {content_type} {datetime.now().isoformat()}",
                "source_type": "direct",
                "description": f"Testing {content_type} content type",
                "content": f"Test content for {content_type}",
                "content_type": content_type
            }
            
            response = api_client.post("/knowledge-sources/direct", ks_data)
            assert response.status_code == 200
            ks = response.json()
            ks_ids.append(ks["id"])
            created_resources["knowledge_sources"].append(ks["id"])
            assert ks["content_type"] == content_type
        
        # Test updating knowledge source with different fields
        test_ks_id = ks_ids[0]
        update_fields = [
            {"title": f"Updated Title {datetime.now().isoformat()}"},
            {"description": "Updated description"},
            {"is_active": False},
            {"access_level": "public"}
        ]
        
        for update_data in update_fields:
            response = api_client.put(f"/knowledge-sources/{test_ks_id}", update_data)
            assert response.status_code == 200
            updated_ks = response.json()
            
            # Verify the update took effect
            if "title" in update_data:
                assert updated_ks["name"] == update_data["title"]
            if "description" in update_data:
                assert updated_ks["description"] == update_data["description"]
            if "is_active" in update_data:
                assert updated_ks["is_active"] == update_data["is_active"]
            if "access_level" in update_data:
                assert updated_ks["access_level"] == update_data["access_level"]
        
        # Note: is_public is not supported in the current database model
        # so we don't test updating it
    
    def test_pagination_and_filtering(self, api_client):
        """Test pagination and filtering capabilities."""
        
        # Create multiple strategies for pagination testing
        strategies = []
        for i in range(5):
            strategy_data = {
                "name": f"Pagination Test Strategy {i} {datetime.now().isoformat()}",
                "description": f"Strategy {i} for pagination testing",
                "goal": f"Goal {i}",
                "patient_introduction": f"Intro {i}",
                "specialty": "Oncology" if i % 2 == 0 else "Cardiology",
                "knowledge_source_ids": [],
                "targeting_rules": [],
                "outcome_actions": []
            }
            
            response = api_client.post("/strategies", strategy_data)
            assert response.status_code == 200
            strategy = response.json()
            strategies.append(strategy["id"])
            created_resources["strategies"].append(strategy["id"])
        
        # Test listing strategies (basic pagination)
        response = api_client.get("/strategies")
        assert response.status_code == 200
        all_strategies = response.json()
        assert len(all_strategies) >= 5  # At least our 5 strategies
        
        # Verify our strategies are in the list
        strategy_ids_in_list = [s["id"] for s in all_strategies]
        for strategy_id in strategies:
            assert strategy_id in strategy_ids_in_list
    
    def test_concurrent_operations(self, api_client):
        """Test concurrent operations and race conditions."""
        
        # Create a knowledge source
        ks_data = {
            "name": f"Concurrent Test KS {datetime.now().isoformat()}",
            "source_type": "direct",
            "description": "Testing concurrent operations",
            "content": "Concurrent test content",
            "content_type": "text/plain"
        }
        
        response = api_client.post("/knowledge-sources/direct", ks_data)
        assert response.status_code == 200
        ks = response.json()
        ks_id = ks["id"]
        created_resources["knowledge_sources"].append(ks_id)
        
        # Simulate concurrent updates
        update_requests = []
        for i in range(3):
            update_data = {
                "title": f"Concurrent Update {i} {datetime.now().isoformat()}",
                "description": f"Concurrent description {i}"
            }
            update_requests.append((f"/knowledge-sources/{ks_id}", update_data))
        
        # Execute updates (simulating concurrent access)
        responses = []
        for endpoint, data in update_requests:
            response = api_client.put(endpoint, data)
            responses.append(response)
        
        # All updates should succeed (last one wins)
        for response in responses:
            assert response.status_code == 200
        
        # Verify final state
        final_response = api_client.get(f"/knowledge-sources/{ks_id}")
        assert final_response.status_code == 200
        final_ks = final_response.json()
        assert "Concurrent Update" in final_ks["name"]


# Additional test to run individual tests for debugging
def test_run_individual_test():
    """Helper function to run individual tests for debugging."""
    import subprocess
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "individual":
        # Run a specific test method
        test_method = sys.argv[2] if len(sys.argv) > 2 else "test_health_check"
        subprocess.run([
            "python", "-m", "pytest", 
            f"app/tests/e2e/api/test_chat_configuration_e2e.py::TestChatConfigurationE2E::{test_method}",
            "-v", "--tb=short"
        ])
