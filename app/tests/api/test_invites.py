import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_invite_unauthenticated():
    payload = {
        "email": "test@x.com",
        "first_name": "Test",
        "last_name": "User",
        "provider_id": "c1"
    }
    response = client.post("/api/generate_invite", json=payload)
    assert response.status_code in (401, 403)
