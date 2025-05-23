import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.services.users import UserService
import uuid

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_auth():
    # Override get_current_active_user to always return a mock user
    class MockUser:
        username = "user"
        email = "user@example.com"
        full_name = "Test User"
        disabled = False
        id = "user-id"
        role = "patient"
    app.dependency_overrides = {}
    from app.api.auth import get_current_active_user
    app.dependency_overrides[get_current_active_user] = lambda: MockUser()
    yield
    app.dependency_overrides = {}

def test_login_success():
    # Insert a real user into the test database
    db = SessionLocal()
    user_service = UserService(db)
    unique_id = str(uuid.uuid4())
    email = f"user_{unique_id}@example.com"
    password = "pass"
    hashed_password = user_service.get_password_hash(password)
    # Clean up any user with the same email before inserting
    db.query(User).filter(User.email == email).delete()
    db.commit()
    user = User(
        id=unique_id,
        email=email,
        hashed_password=hashed_password,
        name="Test User",
        role=UserRole.PATIENT,
        is_active=True
    )
    db.add(user)
    db.commit()
    try:
        response = client.post("/api/auth/token", data={"username": email, "password": password})
        assert response.status_code == 200
        assert "access_token" in response.json()
    finally:
        db.delete(user)
        db.commit()
        db.close()

def test_login_failure(monkeypatch):
    from app.api import auth
    monkeypatch.setattr(auth, "authenticate_user", lambda db, username, password: False)
    response = client.post("/api/auth/token", data={"username": "user", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
