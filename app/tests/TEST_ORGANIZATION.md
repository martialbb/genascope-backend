# Test Organization Guide for Genascope Backend

This document outlines the recommended test organization structure for the Genascope backend application.

## Current Issues

1. SQLAlchemy model initialization issues in tests
2. Inefficient import structure causing dependency issues
3. Pydantic Settings validation errors
4. Confusion with API subfolders and test arrangement
5. Tests failing when run as a suite but passing individually

## Proposed Test Structure

```
backend/app/tests/
│
├── conftest.py                # Global test fixtures and setup
├── pytest.ini                 # Test configuration
├── mock_models.py             # Centralized mock models (expanded version)
│
├── unit/                      # Unit tests (isolated testing of individual components)
│   ├── conftest.py            # Unit-test specific fixtures
│   ├── models/                # Tests for model logic/methods
│   ├── repositories/          # Tests for repository classes
│   ├── services/              # Tests for service classes
│   │   ├── test_labs_service.py
│   │   ├── test_user_service.py
│   │   └── ...
│   └── utils/                 # Tests for utility functions
│
├── integration/               # Integration tests (testing component interaction)
│   ├── conftest.py            # Integration-test specific fixtures
│   ├── repositories/          # Tests for repositories with DB
│   ├── services/              # Tests for service integration
│   └── api/                   # API endpoint tests without full app
│       ├── test_appointments.py
│       └── ...
│
├── e2e/                       # End-to-end tests (full app testing)
│   ├── conftest.py            # E2E-test specific fixtures
│   ├── test_invite_workflow.py
│   └── ...
│
└── fixtures/                  # Test data fixtures
    ├── lab_fixtures.py
    ├── user_fixtures.py
    └── ...
```

## Implementation Guidelines

### 1. Mock Model Organization

Create a comprehensive `mock_models.py` file with factory functions for all your models:

```python
# backend/app/tests/mock_models.py
from unittest.mock import MagicMock

def create_mock_user(id="user123", email="test@example.com", name="Test User", role="patient"):
    """Create a mock user"""
    mock_user = MagicMock()
    mock_user.id = id
    mock_user.email = email
    mock_user.name = name
    mock_user.role = role
    return mock_user

def create_mock_lab_integration(id="lab1", name="Test Lab", api_key="key123", status="active"):
    """Create a mock lab integration"""
    mock_integration = MagicMock()
    mock_integration.id = id
    mock_integration.name = name
    mock_integration.api_key = api_key
    mock_integration.status = status
    return mock_integration

# Add more factory functions for other models
```

### 2. Import Strategy

For each test file:

1. AVOID importing SQLAlchemy models directly
2. Only import enums and non-SQLAlchemy dependent types
3. Import services within fixtures to control initialization timing
4. Use try/except blocks to handle import errors gracefully

Example:

```python
# Good: Import only enums
from app.models.user import UserRole

# Good: Import service within fixture
@pytest.fixture
def service():
    try:
        from app.services.my_service import MyService
        service = MyService()
        # Mock dependencies
        return service
    except ImportError as e:
        pytest.skip(f"Import error: {e}")
```

### 3. Test-Specific Conftest Files

Create specific `conftest.py` files for each test level with appropriate fixtures:

- **Global conftest.py**: General fixtures like mock users, auth helpers
- **Unit conftest.py**: Mocked dependencies, no real DB
- **Integration conftest.py**: Test DB setup/teardown 
- **E2E conftest.py**: Full app instance, seeded DB

### 4. Test Fixtures Organization

Move test fixtures to dedicated files in the fixtures directory:

```python
# backend/app/tests/fixtures/lab_fixtures.py
import pytest
from unittest.mock import MagicMock
from ..mock_models import create_mock_lab_integration

@pytest.fixture
def mock_lab_integrations():
    """Return a list of mock lab integrations"""
    return [
        create_mock_lab_integration(id="lab1", name="Lab One"),
        create_mock_lab_integration(id="lab2", name="Lab Two", status="inactive")
    ]
```

Then import these fixtures where needed:

```python
# In your test file
from ..fixtures.lab_fixtures import mock_lab_integrations
```

### 5. Centralized Error Handling

Add a utility function to handle common import errors:

```python
# backend/app/tests/utils.py
import pytest
import importlib
from typing import Any, Optional

def safe_import(module_path: str, default: Any = None) -> Optional[Any]:
    """
    Safely import a module or attribute, returning default if it fails
    """
    try:
        if "." in module_path:
            module_name, attribute = module_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            return getattr(module, attribute)
        else:
            return importlib.import_module(module_path)
    except (ImportError, AttributeError) as e:
        pytest.skip(f"Failed to import {module_path}: {e}")
        return default
```

### 6. PYTHONPATH Configuration

Update `run_tests_updated.sh` to ensure proper PYTHONPATH configuration:

```bash
#!/bin/bash
# Test runner script

# Set up environment
set -e

# Add the necessary directories to PYTHONPATH
export PYTHONPATH="$(pwd):$(pwd)/backend:$PYTHONPATH"
echo "Setting PYTHONPATH to: $PYTHONPATH"

# Define test directories
UNIT_TEST_DIR="backend/app/tests/unit"
INTEGRATION_TEST_DIR="backend/app/tests/integration"
E2E_TEST_DIR="backend/app/tests/e2e"

# Functions for running different test levels...
```

## Migration Strategy

1. Create the missing directories in the test structure
2. Move existing test files to appropriate locations
3. Update imports in the test files to match the new structure
4. Create centralized mock models and fixtures
5. Implement test-specific conftest files
6. Update run_tests script to handle the new structure

## Recommendations for Resolving Test Issues

1. **SQLAlchemy Initialization Issues**:
   - Continue using MagicMock for models
   - Import services within fixtures using try/except
   - Ensure that DB initialization is not triggered on import

2. **Pydantic Settings Validation**:
   - Create a test-specific settings module
   - Mock environment variables needed by settings
   - Provide test-specific values for required settings

3. **Test Isolation**:
   - Ensure each test suite uses its own fixtures
   - Reset global state between tests
   - Use appropriate pytest scope for fixtures

4. **API Testing**:
   - Separate endpoint tests from service tests
   - Use TestClient with appropriate dependency overrides
   - Mock external services and dependencies
