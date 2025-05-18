# fixtures/settings_fixtures.py
"""
Settings-related fixtures to avoid Pydantic validation errors.
"""
import pytest
from unittest.mock import patch
import os

@pytest.fixture
def mock_settings():
    """
    Mock environment variables for Pydantic settings.
    This avoids validation errors when settings are imported.
    
    Returns a dictionary of the mocked environment variables.
    """
    env_vars = {
        # Database settings
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/test_db',
        
        # Authentication settings
        'SECRET_KEY': 'testing_secret_key_for_jwt_tokens',
        'ALGORITHM': 'HS256',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        
        # API settings
        'API_BASE_URL': 'http://localhost:8000',
        'FRONTEND_URL': 'http://localhost:3000',
        
        # Email settings
        'SMTP_SERVER': 'localhost',
        'SMTP_PORT': '1025',
        'SMTP_USERNAME': 'test_user',
        'SMTP_PASSWORD': 'test_password',
        'SENDER_EMAIL': 'test@example.com',
        'EMAIL_ENABLED': 'false',
        
        # Lab integration settings
        'LAB_API_BASE_URL': 'http://localhost:9000',
        'LAB_API_KEY': 'test_lab_api_key',
        
        # Other settings
        'ENVIRONMENT': 'test',
        'LOG_LEVEL': 'INFO',
    }
    
    with patch.dict('os.environ', env_vars):
        yield env_vars


@pytest.fixture
def patch_settings_module():
    """
    Create a function to patch a specific settings module.
    
    This is useful when you need to mock a specific settings module
    rather than just setting environment variables.
    """
    def _patch_settings(module_path, **kwargs):
        settings_patch = patch(module_path)
        mock_settings = settings_patch.start()
        
        # Set attributes on the mock settings
        for key, value in kwargs.items():
            setattr(mock_settings, key, value)
        
        return mock_settings, settings_patch
    
    return _patch_settings


@pytest.fixture
def with_test_settings():
    """
    Apply test settings by patching environment variables.
    This is an autouse fixture that will apply for all tests.
    """
    with patch.dict('os.environ', {
        'ENVIRONMENT': 'test',
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/test_db',
        'SECRET_KEY': 'testing_secret_key',
        'EMAIL_ENABLED': 'false',
    }):
        yield
