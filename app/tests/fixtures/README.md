# Test Fixtures

This directory contains test data fixtures and configuration files used across the test suite.

## Files

### Database Fixtures
- `db_fixtures.py` - Database connection and session fixtures
- `user_fixtures.py` - User model test fixtures
- `invite_fixtures.py` - Patient invite test fixtures
- `appointment_fixtures.py` - Appointment test fixtures
- `lab_fixtures.py` - Laboratory test fixtures
- `repository_fixtures.py` - Repository layer fixtures
- `integration_fixtures.py` - Integration test fixtures
- `api_fixtures.py` - API endpoint fixtures
- `settings_fixtures.py` - Application settings fixtures
- `lab_webhook_fixtures.py` - Lab webhook test fixtures

### Test Data
- `insert_test_data.sql` - PostgreSQL test data script for creating minimal test accounts, users, and patients

## Usage

Import fixtures in your test files:

```python
from backend.app.tests.fixtures.user_fixtures import test_user, admin_user
from backend.app.tests.fixtures.invite_fixtures import sample_invite
```

## Test Data SQL

The `insert_test_data.sql` file contains PostgreSQL-compatible SQL statements to populate the database with:
- Test hospital accounts
- Users with different roles (super_admin, admin, clinician)
- Sample patient data
- Basic configuration data

Execute with:
```bash
psql -d genascope_test < insert_test_data.sql
```
