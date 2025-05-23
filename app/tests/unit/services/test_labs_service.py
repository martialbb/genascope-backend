"""
Unit tests for the LabService
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from datetime import datetime

from app.services.labs import LabService

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def lab_service(mock_db):
    return LabService(mock_db)

def test_order_test_success(lab_service):
    result = lab_service.order_test('pid', 'CBC', 'cid', notes='Urgent')
    assert result['order_id'].startswith('ORD-')
    assert result['patient_id'] == 'pid'
    assert result['test_type'] == 'CBC'
    assert result['status'] == 'ordered'
    assert result['ordered_by'] == 'cid'
    assert 'ordered_at' in result
    assert result['notes'] == 'Urgent'

def test_order_test_exception(lab_service, monkeypatch):
    def raise_exc(*a, **kw):
        raise Exception('fail')
    monkeypatch.setattr('app.services.labs.datetime', None)  # force error
    with pytest.raises(HTTPException) as excinfo:
        lab_service.order_test('pid', 'CBC', 'cid')
    assert excinfo.value.status_code == 500
    assert 'Failed to order lab test' in str(excinfo.value.detail)

def test_get_results_success(lab_service):
    result = lab_service.get_results('ORD-123')
    assert result['order_id'] == 'ORD-123'
    assert result['status'] == 'completed'
    assert 'results' in result
    assert 'completed_at' in result

def test_get_results_exception(lab_service, monkeypatch):
    def raise_exc(*a, **kw):
        raise Exception('fail')
    monkeypatch.setattr('app.services.labs.datetime', None)  # force error
    with pytest.raises(HTTPException) as excinfo:
        lab_service.get_results('ORD-123')
    assert excinfo.value.status_code == 500
    assert 'Failed to retrieve lab results' in str(excinfo.value.detail)

def test_list_available_tests_success(lab_service):
    tests = lab_service.list_available_tests()
    assert isinstance(tests, list)
    assert any(t['test_id'] == 'CBC' for t in tests)
    assert any(t['test_id'] == 'BRCA' for t in tests)
    assert any(t['test_id'] == 'HER2' for t in tests)

def test_list_available_tests_exception_real(lab_service):
    # Patch api_key to None to trigger the error branch
    lab_service.api_key = None
    with pytest.raises(HTTPException) as excinfo:
        lab_service.list_available_tests()
    assert excinfo.value.status_code == 500
    assert 'Failed to list available tests' in str(excinfo.value.detail)
