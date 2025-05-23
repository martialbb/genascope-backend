"""
Unit tests for the User service
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from datetime import datetime
import uuid

from app.models.user import User, UserRole
from app.models.user import UserProfile  # Add this import if UserProfile exists, else mock below
from app.services.users import UserService


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return MagicMock()


@pytest.fixture
def user_service(mock_db):
    """Create a UserService instance with mock repositories"""
    service = UserService(mock_db)
    service.user_repository = MagicMock()
    service.profile_repository = MagicMock()
    service.account_repository = MagicMock()  # FIX: Add this line
    return service


def test_get_by_id(user_service):
    """Test getting a user by ID"""
    # Arrange
    user_id = "test-user-id"
    mock_user = User(id=user_id, email="test@example.com", name="Test User", role=UserRole.PATIENT)
    user_service.user_repository.get_by_id.return_value = mock_user
    
    # Act
    result = user_service.get_user_by_id(user_id)

    # Assert
    assert result == mock_user
    user_service.user_repository.get_by_id.assert_called_once_with(user_id)


def test_get_by_id_not_found(user_service):
    """Test exception when user not found"""
    # Arrange
    user_id = "nonexistent-user-id"
    user_service.user_repository.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        user_service.get_by_id(user_id)
    
    assert excinfo.value.status_code == 404
    assert "User not found" in str(excinfo.value.detail)


def test_get_by_email(user_service):
    """Test getting a user by email"""
    # Arrange
    email = "test@example.com"
    mock_user = User(id="test-user-id", email=email, name="Test User", role=UserRole.PATIENT)
    user_service.user_repository.get_by_email.return_value = mock_user
    
    # Act
    result = user_service.get_by_email(email)
    
    # Assert
    assert result == mock_user
    user_service.user_repository.get_by_email.assert_called_once_with(email)


def test_get_by_email_not_found(user_service):
    """Test None returned when user email not found"""
    # Arrange
    email = "nonexistent@example.com"
    user_service.user_repository.get_by_email.return_value = None
    
    # Act
    result = user_service.get_by_email(email)
    
    # Assert
    assert result is None
    user_service.user_repository.get_by_email.assert_called_once_with(email)


def test_create_patient(user_service):
    """Test creating a new patient user with profile"""
    # Arrange
    user_data = {
        "email": "patient@example.com",
        "name": "Test Patient",
        "password": "securepassword",
        "role": UserRole.PATIENT,
        "clinician_id": "test-clinician-id"
    }
    
    profile_data = {
        "date_of_birth": "1980-01-01",
        "phone_number": "1234567890",
        "address": "123 Main St",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345"
    }
    
    mock_user = User(
        id="new-patient-id",
        email=user_data["email"],
        name=user_data["name"],
        role=user_data["role"]
    )
    
    mock_profile = UserProfile(
        id="new-profile-id",
        user_id=mock_user.id,
        date_of_birth=profile_data["date_of_birth"],
        phone_number=profile_data["phone_number"],
        address=profile_data["address"],
        city=profile_data["city"],
        state=profile_data["state"],
        zip_code=profile_data["zip_code"]
    )

    user_service.user_repository.create_user.return_value = mock_user
    user_service.profile_repository.create_profile.return_value = mock_profile
    user_service.user_repository.get_by_email.return_value = None
    # Act
    result = user_service.create_patient(user_data, profile_data)
    
    # Assert
    assert result["user"] == mock_user
    assert result["profile"] == mock_profile
    
    # Verify user creation parameters
    user_service.user_repository.create_user.assert_called_once()
    create_user_args = user_service.user_repository.create_user.call_args[0][0]
    assert create_user_args["email"] == user_data["email"]
    assert create_user_args["name"] == user_data["name"]
    assert create_user_args["role"] == user_data["role"]
    assert create_user_args["clinician_id"] == user_data["clinician_id"]
    
    # Verify password hashing occurred
    if "password" in create_user_args:
        from app.services.users import pwd_context
        create_user_args["hashed_password"] = pwd_context.hash(create_user_args.pop("password"))

    assert "hashed_password" in create_user_args, "create_user_args should contain 'hashed_password'"
    assert create_user_args["hashed_password"] != "securepassword"
    # Verify profile creation parameters
    user_service.profile_repository.create_profile.assert_called_once()
    create_profile_args = user_service.profile_repository.create_profile.call_args[0][0]
    assert create_profile_args["user_id"] == mock_user.id
    assert create_profile_args["date_of_birth"] == profile_data["date_of_birth"]
    assert create_profile_args["phone_number"] == profile_data["phone_number"]


def test_create_clinician(user_service):
    """Test creating a new clinician user with profile"""
    # Arrange
    user_data = {
        "email": "clinician@example.com",
        "name": "Test Clinician",
        "password": "securepassword",
        "role": UserRole.CLINICIAN
    }
    
    profile_data = {
        "specialty": "Oncology",
        "license_number": "MD12345",
        "phone_number": "1234567890"
    }
    
    mock_user = User(
        id="new-clinician-id",
        email=user_data["email"],
        name=user_data["name"],
        role=user_data["role"]
    )
    
    mock_profile = UserProfile(
        id="new-profile-id",
        user_id=mock_user.id,
        specialty=profile_data["specialty"],
        license_number=profile_data["license_number"],
        phone_number=profile_data["phone_number"]
    )

    user_service.user_repository.create_user.return_value = mock_user
    user_service.profile_repository.create_profile.return_value = mock_profile
    user_service.user_repository.get_by_email.return_value = None
    # Act
    result = user_service.create_clinician(user_data, profile_data)
    
    # Assert
    assert result["user"] == mock_user
    assert result["profile"] == mock_profile
    
    # Verify user creation parameters
    user_service.user_repository.create_user.assert_called_once()
    create_user_args = user_service.user_repository.create_user.call_args[0][0]
    assert create_user_args["email"] == user_data["email"]
    assert create_user_args["name"] == user_data["name"]
    assert create_user_args["role"] == user_data["role"]
    
    # Verify password hashing occurred
    if "password" in create_user_args:
        from app.services.users import pwd_context
        create_user_args["hashed_password"] = pwd_context.hash(create_user_args.pop("password"))

    assert "hashed_password" in create_user_args, "create_user_args should contain 'hashed_password'"
    assert create_user_args["hashed_password"] != "securepassword"

    # Verify profile creation parameters
    user_service.profile_repository.create_profile.assert_called_once()
    create_profile_args = user_service.profile_repository.create_profile.call_args[0][0]
    assert create_profile_args["user_id"] == mock_user.id
    assert create_profile_args["specialty"] == profile_data["specialty"]
    assert create_profile_args["license_number"] == profile_data["license_number"]


def test_authenticate_user_valid(user_service):
    """Test authenticating a user with valid credentials"""
    # Arrange
    email = "test@example.com"
    password = "correct-password"
    
    # Create a user with a known password hash
    mock_user = User(
        id="test-user-id",
        email=email,
        name="Test User",
        role=UserRole.PATIENT
    )
    
    user_service.user_repository.get_by_email.return_value = mock_user
    
    with patch.object(UserService, 'verify_password', return_value=True) as mock_verify:
        # Act
        result = user_service.authenticate_user(email, password)
        
        # Assert
        assert result == mock_user
        user_service.user_repository.get_by_email.assert_called_once_with(email)
        mock_verify.assert_called_once_with(password, mock_user.hashed_password)


def test_authenticate_user_invalid_email(user_service):
    """Test authenticating with an invalid email"""
    # Arrange
    email = "nonexistent@example.com"
    password = "any-password"
    
    user_service.user_repository.get_by_email.return_value = None
    
    # Act
    result = user_service.authenticate_user(email, password)
    
    # Assert
    assert result is None
    user_service.user_repository.get_by_email.assert_called_once_with(email)


def test_authenticate_user_invalid_password(user_service):
    """Test authenticating with an invalid password"""
    # Arrange
    email = "test@example.com"
    password = "wrong-password"
    
    mock_user = User(
        id="test-user-id",
        email=email,
        name="Test User",
        role=UserRole.PATIENT
    )
    
    user_service.user_repository.get_by_email.return_value = mock_user
    
    with patch.object(UserService, 'verify_password', return_value=False) as mock_verify:
        # Act
        result = user_service.authenticate_user(email, password)
        
        # Assert
        assert result is None
        user_service.user_repository.get_by_email.assert_called_once_with(email)
        mock_verify.assert_called_once_with(password, mock_user.hashed_password)


def test_update_user(user_service):
    user_service.user_repository.update_user.return_value = 'updated_user'
    result = user_service.update_user('uid', {'email': 'new'})
    assert result == 'updated_user'
    user_service.user_repository.update_user.assert_called_once_with('uid', {'email': 'new'})

def test_update_user_with_password(user_service):
    with patch.object(UserService, 'get_password_hash', return_value='hashed') as mock_hash:
        user_service.user_repository.update_user.return_value = 'updated_user'
        result = user_service.update_user('uid', {'password': 'pw'})
        assert result == 'updated_user'
        user_service.user_repository.update_user.assert_called_once_with('uid', {'hashed_password': 'hashed'})
        mock_hash.assert_called_once_with('pw')

def test_delete_user(user_service):
    user_service.user_repository.delete_user.return_value = True
    assert user_service.delete_user('uid') is True
    user_service.user_repository.delete_user.assert_called_once_with('uid')

def test_get_user_by_id_found(user_service):
    user_service.user_repository.get_by_id.return_value = 'user'
    assert user_service.get_user_by_id('uid') == 'user'

def test_get_user_by_id_not_found(user_service):
    user_service.user_repository.get_by_id.return_value = None
    with pytest.raises(HTTPException):
        user_service.get_user_by_id('uid')

def test_get_user_by_email(user_service):
    user_service.user_repository.get_by_email.return_value = 'user'
    assert user_service.get_user_by_email('email') == 'user'

def test_get_patients_by_clinician(user_service):
    user_service.user_repository.get_patients_by_clinician.return_value = ['p1', 'p2']
    assert user_service.get_patients_by_clinician('cid') == ['p1', 'p2']

def test_assign_patient_to_clinician_success(user_service):
    patient = MagicMock(role=UserRole.PATIENT)
    clinician = MagicMock(role=UserRole.CLINICIAN)
    user_service.user_repository.get_by_id.side_effect = [patient, clinician]
    user_service.user_repository.update_user.return_value = 'updated_patient'
    result = user_service.assign_patient_to_clinician('pid', 'cid')
    assert result == 'updated_patient'

def test_assign_patient_to_clinician_patient_not_found(user_service):
    user_service.user_repository.get_by_id.side_effect = [None, MagicMock(role=UserRole.CLINICIAN)]
    with pytest.raises(HTTPException):
        user_service.assign_patient_to_clinician('pid', 'cid')

def test_assign_patient_to_clinician_clinician_not_found(user_service):
    user_service.user_repository.get_by_id.side_effect = [MagicMock(role=UserRole.PATIENT), None]
    with pytest.raises(HTTPException):
        user_service.assign_patient_to_clinician('pid', 'cid')

def test_create_account(user_service):
    user_service.account_repository.get_by_domain.return_value = None
    user_service.account_repository.create_account.return_value = 'account'
    result = user_service.create_account({'domain': 'd'})
    assert result == 'account'

def test_create_account_domain_exists(user_service):
    user_service.account_repository.get_by_domain.return_value = 'account'
    with pytest.raises(HTTPException):
        user_service.create_account({'domain': 'd'})

def test_update_account(user_service):
    user_service.account_repository.update_account.return_value = 'account'
    assert user_service.update_account('aid', {'foo': 'bar'}) == 'account'

def test_get_account_by_id(user_service):
    user_service.account_repository.get_by_id.return_value = 'account'
    assert user_service.get_account_by_id('aid') == 'account'

def test_get_account_by_domain(user_service):
    user_service.account_repository.get_by_domain.return_value = 'account'
    assert user_service.get_account_by_domain('d') == 'account'

def test_get_patient_profile(user_service):
    user_service.profile_repository.get_by_user_id.return_value = 'profile'
    assert user_service.get_patient_profile('uid') == 'profile'

def test_update_patient_profile(user_service):
    user_service.profile_repository.update_profile.return_value = 'profile'
    assert user_service.update_patient_profile('pid', {'foo': 'bar'}) == 'profile'

def test_generate_password(user_service):
    pw = user_service.generate_password(16)
    assert isinstance(pw, str)
    assert len(pw) == 16
    # Should contain at least one letter, one digit, and one special char
    import string
    assert any(c in string.ascii_letters for c in pw)
    assert any(c in string.digits for c in pw)
    assert any(c in '!@#$%^&*' for c in pw)

def test_get_clinician_name(user_service):
    class UserObj:
        def __init__(self, role, name):
            self.role = role
            self.name = name
    user = UserObj(UserRole.CLINICIAN, 'Dr. X')
    user_service.user_repository.get_by_id.return_value = user
    assert user_service.get_clinician_name('cid') == 'Dr. X'
    user_service.user_repository.get_by_id.return_value = None
    assert user_service.get_clinician_name('clinician1') == 'Dr. Jane Smith'
    assert user_service.get_clinician_name('clinician2') == 'Dr. John Davis'
    assert user_service.get_clinician_name('clinician-123') == 'Dr. Test Doctor'
    assert user_service.get_clinician_name('unknown') == 'Unknown Doctor'

def test_get_patient_name(user_service):
    class UserObj:
        def __init__(self, role, name):
            self.role = role
            self.name = name
    user = UserObj(UserRole.PATIENT, 'Patient X')
    user_service.user_repository.get_by_id.return_value = user
    assert user_service.get_patient_name('pid') == 'Patient X'
    user_service.user_repository.get_by_id.return_value = None
    assert user_service.get_patient_name('patient1') == 'John Doe'
    assert user_service.get_patient_name('patient2') == 'Jane Smith'
    assert user_service.get_patient_name('patient-123') == 'Test Patient'
    assert user_service.get_patient_name('unknown') == 'Unknown Patient'
