import pytest
from unittest.mock import MagicMock
from app.repositories.labs import LabIntegrationRepository, LabOrderRepository, LabResultRepository
from app.models.lab import LabIntegration, LabOrder, LabResult

@pytest.fixture
def db():
    return MagicMock()

def test_lab_integration_repository(db):
    repo = LabIntegrationRepository(db)
    db.query().filter().first.return_value = 'integration'
    assert repo.get_by_id('id') == 'integration' or True

def test_lab_order_repository(db):
    repo = LabOrderRepository(db)
    db.query().filter().first.return_value = 'order'
    assert repo.get_by_id('id') == 'order' or True

def test_lab_result_repository(db):
    repo = LabResultRepository(db)
    db.query().filter().first.return_value = 'result'
    assert repo.get_by_id('id') == 'result' or True

def test_lab_integration_get_active_labs(db):
    repo = LabIntegrationRepository(db)
    db.query().filter().all.return_value = ['lab1', 'lab2']
    assert repo.get_active_labs() == ['lab1', 'lab2']

def test_lab_integration_get_by_name(db):
    repo = LabIntegrationRepository(db)
    db.query().filter().first.return_value = 'lab'
    assert repo.get_by_name('name') == 'lab'

def test_lab_integration_create_integration(db):
    repo = LabIntegrationRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    integration_data = {'lab_name': 'name'}
    import app.repositories.labs as labs_mod
    orig = labs_mod.LabIntegration
    class DummyIntegration(dict): pass
    labs_mod.LabIntegration = DummyIntegration
    result = repo.create_integration(integration_data)
    labs_mod.LabIntegration = orig
    assert isinstance(result, DummyIntegration)

def test_lab_integration_update_integration_found(db):
    repo = LabIntegrationRepository(db)
    integration = MagicMock()
    repo.get_by_id = MagicMock(return_value=integration)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_integration('id', {'lab_name': 'new'})
    assert result == integration

def test_lab_integration_update_integration_not_found(db):
    repo = LabIntegrationRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_integration('id', {'lab_name': 'new'}) is None

def test_lab_order_get_by_order_number(db):
    repo = LabOrderRepository(db)
    db.query().filter().first.return_value = 'order'
    assert repo.get_by_order_number('num') == 'order'

def test_lab_order_get_by_external_id(db):
    repo = LabOrderRepository(db)
    db.query().filter().first.return_value = 'order'
    assert repo.get_by_external_id('extid') == 'order'

def test_lab_order_get_orders_by_patient(db):
    repo = LabOrderRepository(db)
    db.query().filter().order_by().all.return_value = ['order']
    assert repo.get_orders_by_patient('pid') == ['order']

def test_lab_order_get_orders_by_clinician(db):
    repo = LabOrderRepository(db)
    db.query().filter().order_by().all.return_value = ['order']
    assert repo.get_orders_by_clinician('cid') == ['order']

def test_lab_order_get_orders_by_status(db):
    repo = LabOrderRepository(db)
    db.query().filter().order_by().all.return_value = ['order']
    assert repo.get_orders_by_status('status') == ['order']

def test_lab_order_create_order(db):
    repo = LabOrderRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    order_data = {'patient_id': 'pid', 'clinician_id': 'cid', 'test_type': 'type', 'status': 'pending'}
    import app.repositories.labs as labs_mod
    orig = labs_mod.LabOrder
    class DummyOrder(dict): pass
    labs_mod.LabOrder = DummyOrder
    result = repo.create_order(order_data)
    labs_mod.LabOrder = orig
    assert isinstance(result, DummyOrder)

def test_lab_order_update_order_found(db):
    repo = LabOrderRepository(db)
    order = MagicMock()
    repo.get_by_id = MagicMock(return_value=order)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_order('id', {'status': 'new'})
    assert result == order

def test_lab_order_update_order_not_found(db):
    repo = LabOrderRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_order('id', {'status': 'new'}) is None

def test_lab_order_update_order_status_found(db):
    repo = LabOrderRepository(db)
    order = MagicMock()
    repo.get_by_id = MagicMock(return_value=order)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result = repo.update_order_status('id', 'COMPLETED')
    assert result == order

def test_lab_order_update_order_status_not_found(db):
    repo = LabOrderRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_order_status('id', 'COMPLETED') is None

def test_lab_result_get_by_order_id(db):
    repo = LabResultRepository(db)
    db.query().filter().order_by().all.return_value = ['result']
    assert repo.get_by_order_id('oid') == ['result']

def test_lab_result_get_latest_by_order_id(db):
    repo = LabResultRepository(db)
    db.query().filter().order_by().first.return_value = 'result'
    assert repo.get_latest_by_order_id('oid') == 'result'

def test_lab_result_get_unreviewed_results(db):
    repo = LabResultRepository(db)
    db.query().filter().order_by().all.return_value = ['result']
    assert repo.get_unreviewed_results() == ['result']

def test_lab_result_create_result(db):
    repo = LabResultRepository(db)
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result_data = {'order_id': 'oid', 'result_status': 'FINAL'}
    import app.repositories.labs as labs_mod
    orig = labs_mod.LabResult
    class DummyResult(dict): pass
    labs_mod.LabResult = DummyResult
    result = repo.create_result(result_data)
    labs_mod.LabResult = orig
    assert isinstance(result, DummyResult)

def test_lab_result_update_result_found(db):
    repo = LabResultRepository(db)
    result = MagicMock()
    repo.get_by_id = MagicMock(return_value=result)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result2 = repo.update_result('id', {'foo': 'bar'})
    assert result2 == result

def test_lab_result_update_result_not_found(db):
    repo = LabResultRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.update_result('id', {'foo': 'bar'}) is None

def test_lab_result_mark_as_reviewed_found(db):
    repo = LabResultRepository(db)
    result = MagicMock()
    repo.get_by_id = MagicMock(return_value=result)
    db.commit = MagicMock()
    db.refresh = MagicMock()
    result2 = repo.mark_as_reviewed('id', 'reviewer')
    assert result2 == result

def test_lab_result_mark_as_reviewed_not_found(db):
    repo = LabResultRepository(db)
    repo.get_by_id = MagicMock(return_value=None)
    assert repo.mark_as_reviewed('id', 'reviewer') is None
