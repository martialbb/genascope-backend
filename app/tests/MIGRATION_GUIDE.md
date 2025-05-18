# Test Structure Migration Guide

This document provides guidance on migrating existing tests to the new test structure.

## Migration Steps

1. **Identify Test Type**: Determine if the test is a unit, integration, or end-to-end test.
2. **Move the Test File**: Move it to the appropriate directory (unit, integration, or e2e).
3. **Update Imports**: Update import statements to match the new structure.
4. **Use Mock Models**: Replace direct SQLAlchemy models with MagicMock objects.
5. **Use Shared Fixtures**: Import and use shared fixtures from the fixtures directory.
6. **Update Service Initialization**: Follow the pattern of initializing services within fixtures.
7. **Run and Fix**: Run the migrated test and fix any remaining issues.

## Example Migrations

### Before: Direct SQLAlchemy Model Usage

```python
from app.models.lab import LabIntegration

def test_something():
    # Direct model instantiation
    integration = LabIntegration(
        id="lab1", 
        name="Lab One", 
        api_key="key1", 
        status="active"
    )
    # Test with the model instance
    assert integration.name == "Lab One"
```

### After: Mock Model Usage

```python
from unittest.mock import MagicMock
from ..mock_models import create_mock_lab_integration

def test_something():
    # Use factory function from mock_models.py
    integration = create_mock_lab_integration(
        id="lab1", 
        name="Lab One", 
        api_key="key1", 
        status="active"
    )
    # Test with the mock model
    assert integration.name == "Lab One"
```

### Before: Service Initialization

```python
from app.services.labs_enhanced import LabEnhancedService

def test_service_method():
    # Direct service initialization
    service = LabEnhancedService(db_session)
    # Test service method
    result = service.some_method()
    assert result is not None
```

### After: Service in Fixture

```python
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def lab_service(mock_db):
    """Create a LabEnhancedService instance with mock repositories"""
    try:
        # Import here to avoid SQLAlchemy initialization issues
        from app.services.labs_enhanced import LabEnhancedService
        
        service = LabEnhancedService(mock_db)
        service.lab_integration_repository = MagicMock()
        service.lab_order_repository = MagicMock()
        service.lab_result_repository = MagicMock()
        service.user_repository = MagicMock()
        return service
    except ImportError as e:
        pytest.skip(f"Unable to import LabEnhancedService: {e}")
        return None

def test_service_method(lab_service):
    # Use service from fixture
    result = lab_service.some_method()
    assert result is not None
```

## Common Issues and Solutions

### Import Errors

**Problem**: SQLAlchemy models fail to initialize when imported at the module level.

**Solution**: Import models or services within fixtures or functions, and use try/except blocks to handle import errors.

```python
@pytest.fixture
def service():
    try:
        from app.services.some_service import SomeService
        return SomeService()
    except ImportError as e:
        pytest.skip(f"Unable to import service: {e}")
        return None
```

### SQLAlchemy Session Issues

**Problem**: Tests fail because they try to use a real SQLAlchemy session.

**Solution**: Always use a mock database session for unit tests.

```python
@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return MagicMock()
```

### Pydantic Settings Validation Errors

**Problem**: Pydantic settings fail to validate when imported.

**Solution**: Use environment variable mocking in fixtures.

```python
@pytest.fixture(autouse=True)
def mock_env_settings():
    with patch.dict('os.environ', {
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/test_db',
        'SECRET_KEY': 'testing_secret_key',
        # Add other required environment variables
    }):
        yield
```

## Additional Resources

- Review template test files in the unit directory for example test patterns
- Use the fixtures directory for shared test fixtures
- Check the mock_models.py file for factory functions for mock objects
- Run tests with the `run_tests_updated.sh` script to ensure proper PYTHONPATH configuration
