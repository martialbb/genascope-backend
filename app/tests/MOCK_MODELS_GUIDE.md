# Working with Mock Models

## Introduction to Mock Models

The mock models system in our test suite addresses a critical issue: avoiding SQLAlchemy model initialization in unit tests. By creating mock objects that mimic our database models, we can test code that depends on these models without requiring a database connection.

## When to Use Mock Models

Use mock models in these scenarios:

1. **Unit testing services**: When testing service logic without database access
2. **Testing API endpoints**: To isolate API logic from database operations
3. **Testing utilities that process model instances**: When you need to process model-like objects

## Mock Model Implementation

Our implementation uses Python's `unittest.mock.MagicMock` to create flexible mock objects. Each model factory function:

1. Creates a MagicMock instance
2. Configures it with properties matching the real model
3. Sets up relationships between models
4. Configures special behavior (like __repr__)

### Example

```python
# Example from mock_models.py
def create_mock_user(id=None, email="test@example.com", name="Test User", 
                    role="patient", hashed_password="hashed_pwd", 
                    is_active=True, created_at=None, updated_at=None):
    """
    Create a mock User instance with specified attributes.
    """
    mock_user = MagicMock()
    mock_user.id = id or str(uuid.uuid4())
    mock_user.email = email
    mock_user.name = name
    mock_user.role = role
    mock_user.hashed_password = hashed_password
    mock_user.is_active = is_active
    mock_user.created_at = created_at or datetime.now()
    mock_user.updated_at = updated_at or datetime.now()
    mock_user.profile = MagicMock()  # For relationship simulation
    
    # Configure the __repr__ method for debugging
    mock_user.__repr__ = lambda self: f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    return mock_user
```

## Core Mock Models

We provide factory functions for all main models:

- `create_mock_user()`: Simulates User model
- `create_mock_lab_integration()`: Simulates LabIntegration model
- `create_mock_lab_order()`: Simulates LabOrder model
- `create_mock_lab_result()`: Simulates LabResult model
- `create_mock_appointment()`: Simulates Appointment model
- ...and more

## Relationships Between Mock Models

Mock models include relationships to simulate the ORM behavior:

```python
# Example of linked mock models
lab_order = create_mock_lab_order(id="order1", patient_id="patient1")
lab_result = create_mock_lab_result(id="result1", lab_order_id="order1")
patient = create_mock_user(id="patient1", role="patient")

# Setup relationships
lab_order.results = [lab_result]
lab_order.patient = patient
lab_result.lab_order = lab_order
patient.lab_orders = [lab_order]
```

## Best Practices

1. **Import selectively**: Import only the specific model factory functions you need
2. **Initialize with defaults**: Let the defaults handle common cases
3. **Configure relationships**: Set up bidirectional relationships when needed
4. **Mock repository methods**: Configure repository mock methods to return your mock models

## Example Usage in Tests

```python
def test_process_lab_order(mock_db):
    # Import mock model factories
    from ...mock_models import (
        create_mock_lab_order,
        create_mock_lab_result,
        create_mock_user
    )
    
    # Create mocks
    lab_order = create_mock_lab_order(status="pending")
    patient = create_mock_user(role="patient")
    lab_order.patient = patient
    
    # Setup service with mock repositories
    service = LabService(mock_db)
    service.lab_order_repository = MagicMock()
    service.lab_order_repository.get_by_id.return_value = lab_order
    
    # Test service method
    result = service.process_order(lab_order.id)
    
    # Assertions
    assert result.status == "processing"
    service.lab_order_repository.update.assert_called_once()
```

## Extending Mock Models

To add a new mock model:

1. Add a new factory function to `mock_models.py`
2. Include all essential attributes matching the real model
3. Set up relationship attributes with MagicMock instances
4. Configure any special behavior needed
5. Document the factory function with docstrings
