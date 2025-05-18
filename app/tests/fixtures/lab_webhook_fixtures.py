# fixtures/lab_webhook_fixtures.py
"""
Lab webhook test fixtures.

This module provides fixtures for testing lab webhook processing,
including the handling of incoming lab results from external systems.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import json
from typing import Dict, List, Any, Optional

from ..mock_models import (
    create_mock_lab_integration,
    create_mock_lab_order,
    create_mock_lab_result,
    create_mock_user
)
from ..utils import safe_import


@pytest.fixture
def lab_webhook_payload_genetic():
    """
    Create a sample genetic test webhook payload.
    
    Returns:
        dict: A webhook payload simulating results from a genetic test
    """
    order_id = str(uuid.uuid4())
    external_id = f"EXT-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "lab_order_id": order_id,
        "external_id": external_id,
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "results": [
            {
                "gene": "BRCA1",
                "variant": "c.68_69delAG",
                "significance": "pathogenic",
                "transcript": "NM_007294.3",
                "genomic_position": "chr17:41276045-41276046",
                "reference": "AG",
                "alternate": "-"
            },
            {
                "gene": "BRCA2",
                "variant": "none detected",
                "significance": "negative",
                "transcript": "NM_000059.3"
            },
            {
                "gene": "TP53",
                "variant": "none detected",
                "significance": "negative",
                "transcript": "NM_000546.5"
            }
        ],
        "summary": {
            "interpretation": "Positive for BRCA1 pathogenic variant",
            "recommendations": "Genetic counseling recommended",
            "clinical_significance": "high"
        },
        "metadata": {
            "lab_name": "LabCorp Genetics",
            "test_type": "Hereditary Cancer Panel",
            "panel_genes": 30,
            "method": "Next-Generation Sequencing",
            "analyst": "J. Smith, PhD",
            "reviewed_by": "A. Johnson, MD"
        }
    }


@pytest.fixture
def lab_webhook_payload_processing():
    """
    Create a sample webhook payload for in-process results.
    
    Returns:
        dict: A webhook payload simulating a processing status update
    """
    order_id = str(uuid.uuid4())
    external_id = f"EXT-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "lab_order_id": order_id,
        "external_id": external_id,
        "status": "processing",
        "timestamp": datetime.now().isoformat(),
        "progress": {
            "current_step": "sample_analysis",
            "percent_complete": 60,
            "estimated_completion": (datetime.now() + timedelta(days=2)).isoformat(),
            "message": "Sample analysis in progress"
        },
        "metadata": {
            "lab_name": "LabCorp Genetics",
            "test_type": "Hereditary Cancer Panel",
            "sample_received_date": (datetime.now() - timedelta(days=1)).isoformat()
        }
    }


@pytest.fixture
def lab_webhook_processor():
    """
    Create a mock lab webhook processor.
    
    This fixture mocks the processor that handles webhooks from lab integrations.
    
    Returns:
        MagicMock: A mock webhook processor
    """
    processor = MagicMock()
    
    # Configure mock methods
    processor.process_genetic_result.return_value = {
        "id": str(uuid.uuid4()),
        "status": "completed",
        "processed": True,
        "timestamp": datetime.now().isoformat()
    }
    
    processor.process_status_update.return_value = {
        "id": str(uuid.uuid4()),
        "status": "updated",
        "processed": True,
        "timestamp": datetime.now().isoformat()
    }
    
    processor.validate_webhook_payload.return_value = True
    
    return processor


@pytest.fixture
def mock_webhook_handler():
    """
    Create a mock webhook route handler.
    
    This fixture provides a mock handler function that can be used to test
    webhook route functionality without triggering actual processing.
    
    Returns:
        function: A mock webhook handler function
    """
    async def mock_handler(request, payload, db):
        # Validate basic payload structure
        if not isinstance(payload, dict):
            return {"error": "Invalid payload format"}
        
        if "lab_order_id" not in payload:
            return {"error": "Missing lab_order_id"}
        
        # Return a success response
        return {
            "received": True,
            "lab_order_id": payload.get("lab_order_id"),
            "status": payload.get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    
    return mock_handler


@pytest.fixture
def setup_lab_webhook_test(lab_integration_repository_mock, lab_order_repository_mock):
    """
    Set up a complete environment for testing lab webhooks.
    
    This fixture combines various mocks to create a complete environment
    for testing the webhook processing flow.
    
    Args:
        lab_integration_repository_mock: Mock lab integration repository
        lab_order_repository_mock: Mock lab order repository
        
    Returns:
        dict: A dictionary containing all mocks and test data
    """
    # Create mock dependencies
    mock_db = MagicMock()
    mock_result_repository = MagicMock()
    
    # Create a test lab order and integration
    lab_integration = create_mock_lab_integration(
        id="webhook_lab",
        name="Webhook Test Lab",
        status="active",
        api_key="webhook_api_key",
        webhook_secret="webhook_secret"
    )
    
    lab_order = create_mock_lab_order(
        id="webhook_order",
        patient_id="webhook_patient",
        clinician_id="webhook_clinician",
        integration_id="webhook_lab",
        status="pending",
        external_id="EXT-12345"
    )
    
    # Configure repositories
    lab_integration_repository_mock.get_by_id.return_value = lab_integration
    lab_order_repository_mock.get_by_id.return_value = lab_order
    lab_order_repository_mock.get_by_external_id.return_value = lab_order
    
    # Mock result creation
    def create_result(result_data):
        return create_mock_lab_result(
            id=str(uuid.uuid4()),
            order_id=lab_order.id,
            status="new",
            result_data=result_data
        )
    
    mock_result_repository.create.side_effect = create_result
    
    # Create webhook processor class mock
    with patch("app.services.lab_webhooks.LabWebhookProcessor") as webhook_processor_class:
        processor_instance = MagicMock()
        webhook_processor_class.return_value = processor_instance
        
        # Configure processor methods
        processor_instance.validate_signature.return_value = True
        processor_instance.process_webhook.return_value = {
            "processed": True,
            "order_id": lab_order.id,
            "result_id": str(uuid.uuid4())
        }
        
        return {
            "db": mock_db,
            "lab_integration": lab_integration,
            "lab_order": lab_order,
            "processor": processor_instance,
            "lab_integration_repository": lab_integration_repository_mock,
            "lab_order_repository": lab_order_repository_mock,
            "lab_result_repository": mock_result_repository
        }


@pytest.fixture
def lab_webhook_verification_token():
    """
    Create a mock function to generate webhook verification tokens.
    
    This fixture provides a function that generates tokens for webhook verification.
    
    Returns:
        function: A token generation function
    """
    def generate_token(lab_id, timestamp=None):
        """Generate a webhook verification token."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # In a real implementation, this would use cryptographic functions
        # For testing, we just concatenate with a secret
        mock_secret = "test_webhook_secret"
        token_data = f"{lab_id}:{timestamp}:{mock_secret}"
        import hashlib
        return hashlib.sha256(token_data.encode()).hexdigest()
    
    return generate_token
