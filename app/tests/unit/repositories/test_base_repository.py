import pytest
from unittest.mock import MagicMock
from app.repositories.base import BaseRepository

class DummyModel:
    id = 1

@pytest.fixture
def db():
    return MagicMock()

def test_base_repository_crud(db):
    repo = BaseRepository(db, DummyModel)
    # Test get_by_id
    db.query().filter().first.return_value = 'obj'
    assert repo.get_by_id(1) == 'obj'
    # Test get_all
    db.query().all.return_value = ['obj1', 'obj2']
    assert repo.get_all() == ['obj1', 'obj2']
    # Test create
    obj = DummyModel()
    repo.create(obj)
    db.add.assert_called_with(obj)
    db.commit.assert_called()
    # Test delete (should delete the object returned by get_by_id)
    db.query().filter().first.return_value = 'obj'
    repo.delete(obj)
    db.delete.assert_called_with('obj')
    db.commit.assert_called()
    # Test update
    repo.update(obj)
    db.commit.assert_called()
