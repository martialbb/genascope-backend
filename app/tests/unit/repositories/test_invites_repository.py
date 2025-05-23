import pytest
from unittest.mock import MagicMock
from app.repositories.invites import InviteRepository
from app.models.invite import PatientInvite

@pytest.fixture
def db():
    return MagicMock()

def test_invite_repository_get_by_id(db):
    repo = InviteRepository(db)
    db.query().filter().first.return_value = 'invite'
    assert repo.get_by_id('id') == 'invite'

def test_invite_repository_get_by_email(db):
    repo = InviteRepository(db)
    db.query().filter().all.return_value = ['invite']
    assert repo.get_by_email('email') == ['invite']

def test_invite_repository_create_and_delete(db):
    repo = InviteRepository(db)
    invite = MagicMock()
    repo.create(invite)
    db.add.assert_called_with(invite)
    db.commit.assert_called()
    # For delete, simulate the repository fetching the object before deleting
    db.query().filter().first.return_value = invite
    repo.delete(invite)
    db.delete.assert_called_with(invite)
    db.commit.assert_called()

def test_invite_repository_get_by_token(db):
    repo = InviteRepository(db)
    db.query().filter().first.return_value = 'invite'
    assert repo.get_by_token('token') == 'invite'

def test_invite_repository_get_active_by_email(db):
    repo = InviteRepository(db)
    db.query().filter().order_by().first.return_value = 'invite'
    assert repo.get_active_by_email('email') == 'invite'

def test_invite_repository_get_by_clinician(db):
    repo = InviteRepository(db)
    db.query().filter().order_by().all.return_value = ['invite']
    assert repo.get_by_clinician('clinician_id') == ['invite']
    # With status
    db.query().filter().filter().order_by().all.return_value = ['invite']
    assert repo.get_by_clinician('clinician_id', status='pending') == ['invite']

def test_invite_repository_create_invite(db):
    repo = InviteRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    invite_data = {'email': 'email', 'clinician_id': 'cid'}
    import app.repositories.invites as invites_mod
    orig = invites_mod.PatientInvite
    class DummyInvite(dict): pass
    invites_mod.PatientInvite = DummyInvite
    result = repo.create_invite(invite_data)
    invites_mod.PatientInvite = orig
    assert isinstance(result, DummyInvite)

def test_invite_repository_update_invite_found(db):
    repo = InviteRepository(db)
    invite = MagicMock()
    repo.get_by_id = MagicMock(return_value=invite)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_invite('id', {'email': 'new'})
    assert result == invite

def test_invite_repository_update_invite_not_found(db):
    repo = InviteRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_invite('id', {'email': 'new'}) is None

def test_invite_repository_mark_as_accepted(db):
    repo = InviteRepository(db)
    repo.update_invite = MagicMock(return_value='invite')
    assert repo.mark_as_accepted('id') == 'invite'

def test_invite_repository_mark_as_expired(db):
    repo = InviteRepository(db)
    repo.update_invite = MagicMock(return_value='invite')
    assert repo.mark_as_expired('id') == 'invite'

def test_invite_repository_revoke_invite(db):
    repo = InviteRepository(db)
    repo.update_invite = MagicMock(return_value='invite')
    assert repo.revoke_invite('id') == 'invite'

def test_invite_repository_cleanup_expired_invites(db):
    repo = InviteRepository(db)
    expired = [MagicMock(id='id1'), MagicMock(id='id2')]
    db.query().filter().all.return_value = expired
    repo.mark_as_expired = MagicMock()
    repo.mark_as_expired.side_effect = lambda id: None
    count = repo.cleanup_expired_invites()
    assert count == 2
