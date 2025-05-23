import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_start_chat_unauthenticated():
    response = client.post("/api/start_chat", json={"patient_id": "p1"})
    assert response.status_code in (401, 403)

def test_submit_answer_unauthenticated():
    response = client.post("/api/submit_answer", json={"session_id": "s1", "question_id": "q1", "answer": "A"})
    assert response.status_code in (401, 403)

def test_get_chat_history_unauthenticated():
    response = client.get("/api/history/s1")
    assert response.status_code in (401, 403)
