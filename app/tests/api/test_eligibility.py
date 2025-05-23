import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_eligibility_unauthenticated():
    response = client.post("/api/eligibility/analyze", json={"session_id": "s1"})
    assert response.status_code in (401, 403)

def test_get_eligibility_unauthenticated():
    response = client.get("/api/eligibility/analyze/s1")
    assert response.status_code in (401, 403)
