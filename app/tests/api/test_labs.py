import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_order_test_unauthenticated():
    response = client.post("/api/labs/order_test", json={"patient_id": "p1", "test_type": "BRCA"})
    assert response.status_code in (401, 403)

def test_get_lab_results_unauthenticated():
    response = client.get("/api/labs/results/order-1")
    assert response.status_code in (401, 403)
