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
        role = "admin"
    app.dependency_overrides = {}
    from app.api.auth import get_current_active_user
    app.dependency_overrides[get_current_active_user] = lambda: MockUser()
    yield
    app.dependency_overrides = {}

def test_create_account_success():
    payload = {
        "email": "test@x.com",
        "name": "Test User",
        "role": "patient",
        "password": "pass12345",
        "confirm_password": "pass12345"
    }
    response = client.post("/api/account/create_user", json=payload)
    assert response.status_code in (200, 201)
    assert "id" in response.json()

def test_create_account_missing_fields():
    # Missing required fields: first_name, last_name, role, password, confirm_password
    response = client.post("/api/account/create_user", json={"email": "test@x.com"})
    assert response.status_code in (400, 422)
