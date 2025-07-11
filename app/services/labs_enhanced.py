"""
Lab service module for business logic related to lab integrations, orders, and results.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
import json
import requests
from datetime import datetime, timedelta

from app.repositories.labs import LabIntegrationRepository, LabOrderRepository, LabResultRepository
from app.repositories.users import UserRepository
from app.repositories.patients import PatientRepository
from app.models.lab import LabIntegration, LabOrder, LabResult, OrderStatus, ResultStatus, TestType
from app.models.user import UserRole
from app.services.base import BaseService
from app.core.config import settings


class LabService(BaseService):
    """
    Service for lab-related operations
    """
    def __init__(self, db: Session):
        self.db = db
        self.integration_repository = LabIntegrationRepository(db)
        self.order_repository = LabOrderRepository(db)
        self.result_repository = LabResultRepository(db)
        self.user_repository = UserRepository(db)
        self.patient_repository = PatientRepository(db)
        self.api_key = settings.LAB_API_KEY
        self.api_url = settings.LAB_API_URL
    
    def get_available_labs(self) -> List[LabIntegration]:
        """
        Get all available lab integrations
        """
        return self.integration_repository.get_active_labs()
    
    def list_available_tests(self) -> List[Dict[str, Any]]:
        """
        List available lab tests
        
        In a real implementation, this would query an external lab API
        """
        try:
            # Mock response for demonstration
            return [
                {
                    "test_id": TestType.BRCA.value,
                    "name": "BRCA Gene Test",
                    "description": "Tests for mutations in the BRCA1 and BRCA2 genes",
                    "turnaround_time_hours": 168  # 7 days
                },
                {
                    "test_id": TestType.GENETIC_PANEL.value,
                    "name": "Comprehensive Genetic Panel",
                    "description": "Tests for multiple gene mutations associated with cancer risk",
                    "turnaround_time_hours": 240  # 10 days
                },
                {
                    "test_id": TestType.MAMMOGRAM.value,
                    "name": "Mammogram",
                    "description": "X-ray imaging of breast tissue",
                    "turnaround_time_hours": 48  # 2 days
                },
                {
                    "test_id": TestType.MRI.value, 
                    "name": "Breast MRI",
                    "description": "Magnetic resonance imaging of breast tissue",
                    "turnaround_time_hours": 72  # 3 days
                },
                {
                    "test_id": TestType.ULTRASOUND.value,
                    "name": "Breast Ultrasound",
                    "description": "Ultrasound imaging of breast tissue",
                    "turnaround_time_hours": 24  # 1 day
                },
                {
                    "test_id": TestType.BIOPSY.value,
                    "name": "Breast Biopsy",
                    "description": "Tissue sample collection and analysis",
                    "turnaround_time_hours": 120  # 5 days
                },
                {
                    "test_id": TestType.BLOOD_TEST.value,
                    "name": "Cancer Biomarker Blood Test",
                    "description": "Blood test for cancer biomarkers",
                    "turnaround_time_hours": 72  # 3 days
                }
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list available tests: {str(e)}")
    
    def create_lab_integration(self, integration_data: Dict[str, Any]) -> LabIntegration:
        """
        Create a new lab integration
        """
        # Check if a lab with this name already exists
        existing = self.integration_repository.get_by_name(integration_data["lab_name"])
        if existing:
            raise HTTPException(status_code=400, detail="A lab with this name already exists")
        
        return self.integration_repository.create_integration(integration_data)
    
    def order_test(self, patient_id: str, test_type: str, clinician_id: str, lab_id: Optional[str] = None, 
                   requisition_details: Optional[Dict[str, Any]] = None, notes: Optional[str] = None) -> LabOrder:
        """
        Order a lab test for a patient
        """
        # Build order data
        order_data = {
            "patient_id": patient_id,
            "ordered_by": clinician_id,  # Fixed: use ordered_by instead of clinician_id
            "order_type": test_type,     # Fixed: use order_type instead of test_type
            # Note: lab_id, requisition_details, notes don't exist in current DB schema
            # "lab_id": lab_id,
            # "requisition_details": requisition_details,
            # "notes": notes
        }
        
        try:
            # Create the order in the database
            order = self.create_lab_order(order_data)
            
            return order
        except Exception as e:
            # Handle errors
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Failed to order lab test: {str(e)}")
    
    def create_lab_order(self, order_data: Dict[str, Any]) -> LabOrder:
        """
        Create a new lab order
        """
        # Validate patient and clinician
        patient = self.patient_repository.get_by_id(order_data["patient_id"])
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        clinician = self.user_repository.get_by_id(order_data["ordered_by"])  # Fixed: use ordered_by
        if not clinician or clinician.role not in [UserRole.CLINICIAN, UserRole.ADMIN]:
            raise HTTPException(status_code=404, detail="Clinician not found")
        
        # Validate lab if provided (note: lab_id field doesn't exist in current schema)
        # if "lab_id" in order_data and order_data["lab_id"]:
        #     lab = self.integration_repository.get_by_id(order_data["lab_id"])
        #     if not lab or not lab.is_active:
        #         raise HTTPException(status_code=404, detail="Lab not found or inactive")
        
        # Create the order
        order = self.order_repository.create_order(order_data)
        
        # Note: lab_id field doesn't exist in current schema, so skip lab API integration
        # If a lab is specified, send the order to the lab's API
        # if order.lab_id:
        #     try:
        #         self._send_order_to_lab(order)
        #     except Exception as e:
        #         # Log the error but don't fail the order creation
        #         print(f"Error sending order to lab: {str(e)}")
        
        return order
    
    def _send_order_to_lab(self, order: LabOrder) -> None:
        """
        Send a lab order to the lab's API
        """
        # Get the lab integration
        lab = self.integration_repository.get_by_id(order.lab_id)
        if not lab:
            raise ValueError("Lab not found")
        
        # Get patient and clinician details
        patient = self.patient_repository.get_by_id(order.patient_id)
        clinician = self.user_repository.get_by_id(order.ordered_by)  # Fixed: use ordered_by
        
        # Create the payload
        payload = {
            "order_id": order.id,  # Use order id since order_number doesn't exist
            "order_type": order.order_type,  # Fixed: use order_type instead of test_type
            "patient": {
                "id": patient.id,
                "name": getattr(patient, 'name', 'Unknown'),
                "email": getattr(patient, 'email', 'Unknown')
            },
            "clinician": {
                "id": clinician.id,
                "name": clinician.name,
                "email": clinician.email
            },
            "lab_reference": order.lab_reference,
            "status": order.status
        }
        
        # Send to lab API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {lab.api_key}"
        }
        
        # In a real implementation, this would actually call the lab's API
        # For now, we just simulate a successful response
        # response = requests.post(lab.api_url, json=payload, headers=headers)
        # if response.status_code != 200:
        #     raise HTTPException(status_code=response.status_code, detail=response.text)
        
        # response_data = response.json()
        response_data = {"external_order_id": f"EXT-{str(uuid.uuid4())[:8]}"}
        
        # Update the order status (can't store external_order_id since field doesn't exist)
        self.order_repository.update_order(order.id, {
            "status": OrderStatus.APPROVED.value
        })
    
    def get_patient_orders(self, patient_id: str) -> List[LabOrder]:
        """
        Get all lab orders for a patient
        """
        return self.order_repository.get_orders_by_patient(patient_id)
    
    def get_clinician_orders(self, clinician_id: str) -> List[LabOrder]:
        """
        Get all lab orders created by a clinician
        """
        return self.order_repository.get_orders_by_clinician(clinician_id)
    
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a lab order
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get the latest result if any
        result = self.result_repository.get_latest_by_order_id(order_id)
        
        # Get patient and clinician details
        patient = self.user_repository.get_by_id(order.patient_id)
        clinician = self.user_repository.get_by_id(order.ordered_by)  # Fixed: use ordered_by
        
        # Get lab details if applicable (note: lab_id field doesn't exist in current schema)
        lab = None
        # if order.lab_id:
        #     lab = self.integration_repository.get_by_id(order.lab_id)
        
        return {
            "order": order,
            "result": result,
            "patient": patient,
            "clinician": clinician,
            "lab": lab
        }
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> LabOrder:
        """
        Update the status of a lab order
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return self.order_repository.update_order_status(order_id, status)
    
    def get_results(self, order_id: str) -> Dict[str, Any]:
        """
        Get test results for a specific order
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        result = self.result_repository.get_latest_by_order_id(order_id)
        if not result:
            raise HTTPException(status_code=404, detail="Results not found for this order")
        
        # Format the response (only using fields that exist in current schema)
        return {
            "order_id": order.id,
            "order_type": order.order_type,  # Fixed: use order_type
            "status": result.status,  # Using actual DB field
            "test_name": result.test_name,
            "result_value": result.result_value,
            "unit": result.unit,
            "reference_range": result.reference_range,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }
    
    def record_lab_result(self, result_data: Dict[str, Any]) -> LabResult:
        """
        Record a new lab result
        """
        # Validate order (using correct field name)
        order = self.order_repository.get_by_id(result_data["lab_order_id"])  # Fixed: use lab_order_id
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Create the result
        result = self.result_repository.create_result(result_data)
        
        # Update order status if completed (using fields that exist in schema)
        if result.status in ['final', 'amended']:
            self.order_repository.update_order_status(order.id, OrderStatus.COMPLETED)
        
        return result
    
    def get_order_results(self, order_id: str) -> List[LabResult]:
        """
        Get all results for a lab order
        """
        # Validate order
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return self.result_repository.get_by_order_id(order_id)
    
    def get_patient_results(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get all lab results for a patient
        """
        # Get all orders for the patient
        orders = self.order_repository.get_orders_by_patient(patient_id)
        
        results = []
        for order in orders:
            latest_result = self.result_repository.get_latest_by_order_id(order.id)
            if latest_result:
                results.append({
                    "order": order,
                    "result": latest_result
                })
        
        return results
    
    def review_result(self, result_id: str, reviewer_id: str) -> LabResult:
        """
        Mark a lab result as reviewed
        """
        # Validate reviewer
        reviewer = self.user_repository.get_by_id(reviewer_id)
        if not reviewer or reviewer.role not in [UserRole.CLINICIAN, UserRole.ADMIN]:
            raise HTTPException(status_code=400, detail="Invalid reviewer")
        
        result = self.result_repository.get_by_id(result_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        return self.result_repository.mark_as_reviewed(result_id, reviewer_id)
    
    def get_unreviewed_results(self) -> List[LabResult]:
        """
        Get all unreviewed results
        """
        return self.result_repository.get_unreviewed_results()
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook from a lab
        """
        # Validate the webhook data
        if "external_order_id" not in webhook_data:
            raise HTTPException(status_code=400, detail="Missing external_order_id")
        
        if "result_status" not in webhook_data or "result_data" not in webhook_data:
            raise HTTPException(status_code=400, detail="Missing result information")
        
        # Find the order
        order = self.order_repository.get_by_external_id(webhook_data["external_order_id"])
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Create or update the result (using fields that exist in current schema)
        result_data = {
            "lab_order_id": order.id,  # Fixed: use lab_order_id
            "test_name": webhook_data.get("test_name", "Unknown Test"),
            "result_value": str(webhook_data.get("result_data", "")),
            "status": webhook_data["result_status"],
            "unit": webhook_data.get("unit", ""),
            "reference_range": webhook_data.get("reference_range", "")
        }
        
        result = self.result_repository.create_result(result_data)
        
        # Update order status (using actual field values)
        if webhook_data["result_status"] == 'final':
            self.order_repository.update_order_status(order.id, OrderStatus.COMPLETED)
        
        return {
            "success": True,
            "order_id": order.id,
            "result_id": result.id
        }
