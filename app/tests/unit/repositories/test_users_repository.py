import pytest
from unittest.mock import MagicMock
from app.repositories.users import UserRepository
from app.models.user import User

@pytest.fixture
def db():
    return MagicMock()

def test_user_repository_get_by_id(db):
    repo = UserRepository(db)
    db.query().filter().first.return_value = 'user'
    assert repo.get_by_id('id') == 'user'

def test_user_repository_get_by_email(db):
    repo = UserRepository(db)
    db.query().filter().first.return_value = 'user'
    assert repo.get_by_email('email') == 'user'

def test_user_repository_get_users_by_account(db):
    repo = UserRepository(db)
    db.query().filter().all.return_value = ['user1', 'user2']
    assert repo.get_users_by_account('account_id') == ['user1', 'user2']

def test_user_repository_get_users_by_role(db):
    repo = UserRepository(db)
    db.query().filter().all.return_value = ['user1', 'user2']
    assert repo.get_users_by_role('role') == ['user1', 'user2']

def test_user_repository_get_patients_by_clinician(db):
    repo = UserRepository(db)
    db.query().filter().all.return_value = ['patient1', 'patient2']
    assert repo.get_patients_by_clinician('clinician_id') == ['patient1', 'patient2']

def test_user_repository_create_user(db):
    repo = UserRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    user_data = {'id': 'id', 'email': 'email'}
    import app.repositories.users as users_mod
    orig = users_mod.User
    class DummyUser(dict): pass
    users_mod.User = DummyUser
    result = repo.create_user(user_data)
    users_mod.User = orig
    assert isinstance(result, DummyUser)

def test_user_repository_update_user_found(db):
    repo = UserRepository(db)
    user = MagicMock()
    repo.get_by_id = MagicMock(return_value=user)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_user('id', {'email': 'new'})
    assert result == user

def test_user_repository_update_user_not_found(db):
    repo = UserRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_user('id', {'email': 'new'}) is None

def test_user_repository_delete_user_found(db):
    repo = UserRepository(db)
    user = MagicMock()
    repo.get_by_id = MagicMock(return_value=user)
    db.delete = MagicMock()
    db.commit = MagicMock()
    assert repo.delete_user('id') is True

def test_user_repository_delete_user_not_found(db):
    repo = UserRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.delete_user('id') is False

# AccountRepository tests
def test_account_repository_get_by_domain(db):
    from app.repositories.users import AccountRepository
    repo = AccountRepository(db)
    db.query().filter().first.return_value = 'account'
    assert repo.get_by_domain('domain') == 'account'

def test_account_repository_get_by_id(db):
    from app.repositories.users import AccountRepository
    repo = AccountRepository(db)
    db.query().filter().first.return_value = 'account'
    assert repo.get_by_id('id') == 'account'

def test_account_repository_create_account(db):
    from app.repositories.users import AccountRepository
    repo = AccountRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    account_data = {'id': 'id', 'domain': 'domain'}
    import app.repositories.users as users_mod
    orig = users_mod.Account
    class DummyAccount(dict): pass
    users_mod.Account = DummyAccount
    result = repo.create_account(account_data)
    users_mod.Account = orig
    assert isinstance(result, DummyAccount)

def test_account_repository_update_account_found(db):
    from app.repositories.users import AccountRepository
    repo = AccountRepository(db)
    account = MagicMock()
    repo.get_by_id = MagicMock(return_value=account)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_account('id', {'domain': 'new'})
    assert result == account

def test_account_repository_update_account_not_found(db):
    from app.repositories.users import AccountRepository
    repo = AccountRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_account('id', {'domain': 'new'}) is None

def test_account_repository_delete_account_found(db):
    from app.repositories.users import AccountRepository
    repo = AccountRepository(db)
    account = MagicMock()
    repo.get_by_id = MagicMock(return_value=account)
    db.delete = MagicMock()
    db.commit = MagicMock()
    assert repo.delete_account('id') is True

def test_account_repository_delete_account_not_found(db):
    from app.repositories.users import AccountRepository
    repo = AccountRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.delete_account('id') is False

# PatientProfileRepository tests
def test_patient_profile_repository_get_by_user_id(db):
    from app.repositories.users import PatientProfileRepository
    repo = PatientProfileRepository(db)
    db.query().filter().first.return_value = 'profile'
    assert repo.get_by_user_id('user_id') == 'profile'

def test_patient_profile_repository_create_profile(db):
    from app.repositories.users import PatientProfileRepository
    repo = PatientProfileRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    profile_data = {'user_id': 'user_id'}
    import app.repositories.users as users_mod
    orig = users_mod.PatientProfile
    class DummyProfile(dict): pass
    users_mod.PatientProfile = DummyProfile
    result = repo.create_profile(profile_data)
    users_mod.PatientProfile = orig
    assert isinstance(result, DummyProfile)

def test_patient_profile_repository_update_profile_found(db):
    from app.repositories.users import PatientProfileRepository
    repo = PatientProfileRepository(db)
    profile = MagicMock()
    repo.get_by_id = MagicMock(return_value=profile)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_profile('id', {'foo': 'bar'})
    assert result == profile

def test_patient_profile_repository_update_profile_not_found(db):
    from app.repositories.users import PatientProfileRepository
    repo = PatientProfileRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_profile('id', {'foo': 'bar'}) is None
