# Testing Organization

This directory contains all the tests for the Genascope backend application. Tests are organized by testing level and by module.

## Test Structure

Tests are organized into three levels:

- **Unit Tests**: Located in `app/tests/unit/`. Tests for individual components in isolation, with all dependencies mocked.
- **Integration Tests**: Located in `app/tests/integration/`. Tests for combinations of components working together, with partial mocking.
- **End-to-End Tests**: Located in `app/tests/e2e/`. Tests that verify the entire application works together from the API endpoint to the database.

Within each level, tests are further organized by module:

- `api/`: Tests for API endpoints
- `services/`: Tests for service layer components
- `repositories/`: Tests for data access layer components

## Running Tests

### Running All Tests

```bash
python -m pytest
```

### Running Tests by Level

```bash
python -m pytest app/tests/unit/  # Run all unit tests
python -m pytest app/tests/integration/  # Run all integration tests
python -m pytest app/tests/e2e/  # Run all end-to-end tests
```

### Running Tests with Markers

```bash
python -m pytest -m unit  # Run all tests with the 'unit' marker
python -m pytest -m integration  # Run all tests with the 'integration' marker
python -m pytest -m e2e  # Run all tests with the 'e2e' marker
```

## Test Configuration

Test configuration is managed in the `pytest.ini` file at the root of the project. This file defines markers and other pytest settings.

## Test Fixtures

Common test fixtures are defined in `app/tests/conftest.py`. These fixtures are available to all tests.

## Best Practices

1. **Use proper mocking**: Always use `@patch` decorators with appropriate return values instead of directly modifying dependencies.
2. **Use JSON body for API updates**: All API tests should send data in the request body as JSON, not as query parameters.
3. **Keep tests independent**: Each test should be able to run independently of other tests.
4. **Mark tests appropriately**: Use the appropriate pytest markers (`unit`, `integration`, `e2e`) to categorize tests.
5. **Follow the test level structure**: Put tests in the appropriate directory based on whether they are unit, integration, or end-to-end tests.
