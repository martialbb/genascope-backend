"""
Lab repository module for handling database operations for lab integrations, orders, and results.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models.lab import LabIntegration, LabOrder, LabResult, OrderStatus, ResultStatus
from app.repositories.base import BaseRepository
import uuid
from datetime import datetime


class LabIntegrationRepository(BaseRepository):
    """Repository for LabIntegration operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, LabIntegration)
    
    def get_active_labs(self) -> List[LabIntegration]:
        """Get all active lab integrations"""
        return self.db.query(LabIntegration).filter(LabIntegration.is_active == True).all()
    
    def get_by_name(self, lab_name: str) -> Optional[LabIntegration]:
        """Get a lab integration by name"""
        return self.db.query(LabIntegration).filter(LabIntegration.lab_name == lab_name).first()
    
    def create_integration(self, integration_data: Dict[str, Any]) -> LabIntegration:
        """Create a new lab integration"""
        if "id" not in integration_data:
            integration_data["id"] = str(uuid.uuid4())
        
        integration = LabIntegration(**integration_data)
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        return integration
    
    def update_integration(self, integration_id: str, update_data: Dict[str, Any]) -> Optional[LabIntegration]:
        """Update a lab integration"""
        integration = self.get_by_id(integration_id)
        if not integration:
            return None
        
        for key, value in update_data.items():
            if hasattr(integration, key):
                setattr(integration, key, value)
        
        integration.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(integration)
        return integration


class LabOrderRepository(BaseRepository):
    """Repository for LabOrder operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, LabOrder)
    
    def get_by_order_number(self, order_number: str) -> Optional[LabOrder]:
        """Get a lab order by its order number"""
        return self.db.query(LabOrder).filter(LabOrder.order_number == order_number).first()
    
    def get_by_external_id(self, external_order_id: str) -> Optional[LabOrder]:
        """Get a lab order by its external order ID"""
        return self.db.query(LabOrder).filter(LabOrder.external_order_id == external_order_id).first()
    
    def get_orders_by_patient(self, patient_id: str) -> List[LabOrder]:
        """Get all lab orders for a patient"""
        return self.db.query(LabOrder).filter(LabOrder.patient_id == patient_id)\
            .order_by(desc(LabOrder.created_at)).all()
    
    def get_orders_by_clinician(self, clinician_id: str) -> List[LabOrder]:
        """Get all lab orders created by a clinician"""
        return self.db.query(LabOrder).filter(LabOrder.clinician_id == clinician_id)\
            .order_by(desc(LabOrder.created_at)).all()
    
    def get_orders_by_status(self, status: OrderStatus) -> List[LabOrder]:
        """Get all lab orders with a specific status"""
        return self.db.query(LabOrder).filter(LabOrder.status == status)\
            .order_by(desc(LabOrder.created_at)).all()
    
    def create_order(self, order_data: Dict[str, Any]) -> LabOrder:
        """Create a new lab order"""
        if "id" not in order_data:
            order_data["id"] = str(uuid.uuid4())
        
        # Generate order number if not provided
        if "order_number" not in order_data:
            order_data["order_number"] = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        order = LabOrder(**order_data)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def update_order(self, order_id: str, update_data: Dict[str, Any]) -> Optional[LabOrder]:
        """Update a lab order"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        for key, value in update_data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        order.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> Optional[LabOrder]:
        """Update a lab order's status"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        order.status = status
        
        # Set date fields based on status
        if status == OrderStatus.COLLECTED:
            order.collection_date = datetime.utcnow()
        elif status == OrderStatus.COMPLETED:
            order.completed_date = datetime.utcnow()
        
        order.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        return order


class LabResultRepository(BaseRepository):
    """Repository for LabResult operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, LabResult)
    
    def get_by_order_id(self, order_id: str) -> List[LabResult]:
        """Get all results for a lab order"""
        return self.db.query(LabResult).filter(LabResult.order_id == order_id)\
            .order_by(desc(LabResult.created_at)).all()
    
    def get_latest_by_order_id(self, order_id: str) -> Optional[LabResult]:
        """Get the latest result for a lab order"""
        return self.db.query(LabResult).filter(LabResult.order_id == order_id)\
            .order_by(desc(LabResult.created_at)).first()
    
    def get_unreviewed_results(self) -> List[LabResult]:
        """Get all unreviewed lab results"""
        return self.db.query(LabResult).filter(
            and_(
                LabResult.reviewed == False,
                LabResult.result_status.in_([ResultStatus.PRELIMINARY, ResultStatus.FINAL])
            )
        ).order_by(desc(LabResult.created_at)).all()
    
    def create_result(self, result_data: Dict[str, Any]) -> LabResult:
        """Create a new lab result"""
        if "id" not in result_data:
            result_data["id"] = str(uuid.uuid4())
        
        result = LabResult(**result_data)
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def update_result(self, result_id: str, update_data: Dict[str, Any]) -> Optional[LabResult]:
        """Update a lab result"""
        result = self.get_by_id(result_id)
        if not result:
            return None
        
        for key, value in update_data.items():
            if hasattr(result, key):
                setattr(result, key, value)
        
        result.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def mark_as_reviewed(self, result_id: str, reviewer_id: str) -> Optional[LabResult]:
        """Mark a lab result as reviewed"""
        result = self.get_by_id(result_id)
        if not result:
            return None
        
        result.reviewed = True
        result.reviewed_by = reviewer_id
        result.reviewed_at = datetime.utcnow()
        result.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(result)
        return result
