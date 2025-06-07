# Security Integration Tests

This directory contains integration tests that verify security features across the application.

## Test Files

### Role-Based Access Control Tests
- `test_comprehensive_security.py` - Comprehensive security verification for invite endpoints
- `test_account_access_control.py` - Tests account-based access control
- `test_account_filtering.py` - Tests filtering based on account permissions
- `test_account_isolation.py` - Tests isolation between different accounts
- `test_simple_security.py` - Basic security verification tests

### Individual Account Tests
- `test_individual_account.py` - Tests individual account functionality
- `test_individual_account_fixed.py` - Fixed version of individual account tests

## Running Tests

```bash
# Run all security integration tests
cd /Users/martial-m1/genascope-frontend/backend
python -m pytest app/tests/integration/security/ -v

# Run specific test file
python -m pytest app/tests/integration/security/test_comprehensive_security.py -v
```

## Test Categories

- **Authentication Tests**: Verify login/logout functionality
- **Authorization Tests**: Verify role-based permissions
- **Account Isolation**: Ensure data isolation between accounts
- **Cross-Account Access**: Verify super admin capabilities

## Prerequisites

- Backend server running on `http://localhost:8000`
- Test database with proper test data
- Valid test user credentials for different roles
