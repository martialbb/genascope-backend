# Invite System Integration Tests

This directory contains integration tests specifically for the patient invite system functionality.

## Test Files

### `test_invite_security.py`
- **Purpose**: Tests role-based access control for the invite system
- **Coverage**: 
  - Super admin access to all invites across accounts
  - Admin access to invites within their account
  - Clinician access to only their own invites
  - Proper 403 Forbidden responses for unauthorized access
- **Test Users**: Uses predefined test users with different roles

### `test_new_patient_invite.py`
- **Purpose**: Tests the complete invite creation and management workflow
- **Coverage**:
  - Creating invites for new patients
  - Email validation and error handling
  - Invite status tracking
  - Database consistency
- **Dependencies**: Requires valid patient data and authenticated users

## Running the Tests

### Individual Test Files
```bash
# Run invite security tests
python -m pytest backend/app/tests/integration/invite_system/test_invite_security.py -v

# Run new patient invite tests
python -m pytest backend/app/tests/integration/invite_system/test_new_patient_invite.py -v
```

### All Invite System Tests
```bash
python -m pytest backend/app/tests/integration/invite_system/ -v
```

## Test Data Requirements

- **Test Users**: Super admin, admin, and clinician users must exist in the database
- **Patients**: Valid patient records with email addresses
- **Authentication**: Tests use JWT tokens for authentication

## Common Issues

1. **Authentication Errors**: Ensure test users exist and have correct passwords
2. **Email Validation**: Patient records must have valid email addresses
3. **Database State**: Old pending invites may need to be expired before testing

## Related Files

- `/backend/app/api/invites.py` - Main invite API endpoints
- `/backend/app/services/invites.py` - Invite business logic
- `/backend/app/tests/scripts/` - Utility scripts for invite testing
