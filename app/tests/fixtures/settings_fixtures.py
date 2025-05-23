import pytest

@pytest.fixture
def mock_settings():
    class Settings:
        DATABASE_URL = 'sqlite:///:memory:'
        SECRET_KEY = 'test_secret_key'
        API_BASE_URL = 'http://localhost:8000'
        ENVIRONMENT = 'test'
    return Settings()

@pytest.fixture
def with_test_settings(monkeypatch, mock_settings):
    monkeypatch.setattr('app.core.config.settings', mock_settings)
    yield
