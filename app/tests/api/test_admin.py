import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_auth():
    class MockUser:
        username = "admin@genascope.com"
        email = "admin@genascope.com"
        full_name = "Admin User"
        disabled = False
        id = "admin-id"
        role = "super_admin"
    app.dependency_overrides = {}
    from app.api.auth import get_current_active_user
    app.dependency_overrides[get_current_active_user] = lambda: MockUser()
    yield
    app.dependency_overrides = {}

def test_create_admin_success():
    payload = {
        "name": "Test Account",
        "domain": "test.com",
        "admin_email": "admin@test.com",
        "admin_name": "Admin User",
        "admin_password": "pass1234",
        "admin_confirm_password": "pass1234",
        "subscription_tier": "basic",
        "max_users": 10
    }
    response = client.post("/api/admin/create_account", json=payload)
    assert response.status_code in (200, 201)
    assert "id" in response.json()

def test_create_admin_missing_fields():
    # Missing required fields: domain, admin_email, admin_name, admin_password, subscription_tier, max_users
    response = client.post("/api/admin/create_account", json={"name": "Test Account"})
    assert response.status_code in (400, 422)
