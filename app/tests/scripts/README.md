# Test Scripts Directory

This directory contains utility scripts for testing, debugging, and data management during development and testing phases.

## Script Files

### Authentication & User Management

#### `check_test_users.py`
- **Purpose**: Verifies test users exist and their authentication credentials
- **Usage**: `python check_test_users.py`
- **Output**: Lists available test users and their roles

#### `test_password.py`
- **Purpose**: Tests password hashing and verification functionality
- **Usage**: `python test_password.py`

#### `generate_hash.py`
- **Purpose**: Generates password hashes for test users
- **Usage**: `python generate_hash.py`

### Integration Testing

#### `test-integration.sh`
- **Purpose**: Full integration test script for frontend-backend API communication
- **Features**:
  - Tests backend authentication
  - Verifies API endpoints
  - Tests data transformation
  - Validates frontend-backend integration
- **Usage**: `bash test-integration.sh`
- **Requirements**: Backend server running on localhost:8000

### Invite System Testing

#### `create_test_invites.py`
- **Purpose**: Creates test invites for development and testing
- **Features**: 
  - Creates invites for different user roles
  - Handles patient email validation
  - Provides detailed output of invite creation process
- **Usage**: `python create_test_invites.py`

#### `create_test_invites_clean.py`
- **Purpose**: Clean version of invite creation with minimal output
- **Usage**: `python create_test_invites_clean.py`

#### `verify_invite_security.py`
- **Purpose**: Comprehensive security testing for invite system
- **Features**:
  - Tests role-based access control
  - Verifies proper authorization
  - Generates detailed security reports
- **Usage**: `python verify_invite_security.py`

### Debugging Scripts

#### `debug_clinician_error.py`
- **Purpose**: Debugging script for clinician-specific invite issues
- **Usage**: `python debug_clinician_error.py`

#### `debug_invite_test.py`
- **Purpose**: General debugging for invite system issues
- **Usage**: `python debug_invite_test.py`

## Running Scripts

### Prerequisites
```bash
# Ensure you're in the backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup
Ensure your `.env` file contains:
```env
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your-secret-key
```

### Running Individual Scripts
```bash
# From the backend directory
python app/tests/scripts/script_name.py
```

## Script Categories

### 🔧 **Utility Scripts**
- `check_test_users.py`
- `generate_hash.py`
- `test_password.py`

### 🧪 **Testing Scripts**
- `create_test_invites.py`
- `create_test_invites_clean.py`
- `verify_invite_security.py`

### 🐛 **Debugging Scripts**
- `debug_clinician_error.py`
- `debug_invite_test.py`

## Common Use Cases

### 1. Setting Up Test Environment
```bash
python app/tests/scripts/check_test_users.py
python app/tests/scripts/create_test_invites.py
```

### 2. Security Testing
```bash
python app/tests/scripts/verify_invite_security.py
```

### 3. Debugging Issues
```bash
python app/tests/scripts/debug_invite_test.py
python app/tests/scripts/debug_clinician_error.py
```

## Notes

- These scripts are for development and testing purposes only
- Do not run against production databases
- Scripts assume test data exists (users, patients, etc.)
- Some scripts may modify database state (creating invites, expiring records)
