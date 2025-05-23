import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_user_unauthenticated():
    response = client.get("/api/users/user-1")
    assert response.status_code in (401, 403)

def test_create_user_unauthenticated():
    response = client.post("/api/users", json={"email": "test@x.com", "password": "pass"})
    assert response.status_code in (401, 403)
