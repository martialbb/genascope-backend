from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.auth import require_full_access, User
from app.services.labs_enhanced import LabService
from app.models.user import UserRole
from app.models.lab import OrderStatus as DBOrderStatus, ResultStatus as DBResultStatus
from app.schemas.labs import (
    LabOrderCreate, LabOrderResponse, LabResultResponse, LabOrderBase,
    TestType, OrderStatus, ResultStatus
)
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/labs", tags=["labs"])

@router.get("/available_tests", response_model=List[Dict[str, Any]])
async def list_available_tests(
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    List available lab tests
    """
    lab_service = LabService(db)
    return lab_service.list_available_tests()

@router.get("/available_labs", response_model=List[Dict[str, Any]])
async def list_available_labs(
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    List available lab partners
    """
    # Only clinicians and admins can view labs
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view lab partners"
        )
    
    lab_service = LabService(db)
    labs = lab_service.get_available_labs()
    
    # Convert to response format
    lab_list = []
    for lab in labs:
        lab_list.append({
            "id": lab.id,
            "name": lab.lab_name,
            "api_url": lab.api_url,
            "is_active": lab.is_active,
            "created_at": lab.created_at
        })
    
    return lab_list

@router.post("/order_test", response_model=LabOrderResponse)
async def order_test(
    test_order: LabOrderCreate,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Submit a laboratory test order
    """
    # Only clinicians and admins can order tests
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to order lab tests"
        )
    
    lab_service = LabService(db)
    
    # Convert from schema enum to DB enum
    test_type = test_order.test_type.value
    
    # Process requisition details
    requisition_details = {}
    if test_order.scheduled_date:
        requisition_details["scheduled_date"] = test_order.scheduled_date
    
    if test_order.facility_id:
        requisition_details["facility_id"] = test_order.facility_id
    
    try:
        # Create the order
        order = lab_service.order_test(
            patient_id=test_order.patient_id,
            test_type=test_type,
            clinician_id=test_order.clinician_id,
            requisition_details=requisition_details,
            notes=test_order.notes
        )
        
        # Get patient and clinician names
        patient = lab_service.user_repository.get_by_id(order.patient_id)
        clinician = lab_service.user_repository.get_by_id(order.ordered_by)  # Fixed: use ordered_by
        
        # Convert DB status to schema enum
        status_map = {
            DBOrderStatus.PENDING: OrderStatus.ORDERED,
            DBOrderStatus.APPROVED: OrderStatus.ORDERED,
            DBOrderStatus.COLLECTED: OrderStatus.SPECIMEN_COLLECTED,
            DBOrderStatus.IN_PROGRESS: OrderStatus.IN_PROCESS,
            DBOrderStatus.COMPLETED: OrderStatus.COMPLETED,
            DBOrderStatus.CANCELLED: OrderStatus.CANCELLED,
            DBOrderStatus.REJECTED: OrderStatus.REJECTED
        }
        
        order_status = OrderStatus.ORDERED
        if order.status in status_map:
            order_status = status_map[order.status]
        
        # Format scheduled date
        scheduled_date = None
        # Note: requisition_details field does not exist in current schema
        if False: # order.requisition_details and "scheduled_date" in order.requisition_details:
            from datetime import datetime
            try:
                scheduled_date = datetime.fromisoformat(order.requisition_details["scheduled_date"]).date()
            except (ValueError, TypeError):
                pass
        
        return LabOrderResponse(
            order_id=order.id,
            patient_id=order.patient_id,
            test_type=test_type,
            clinician_id=order.ordered_by,  # Fixed: use ordered_by
            notes=getattr(order, 'notes', ''),  # Handle missing notes field
            status=order_status,
            ordered_at=order.created_at,
            scheduled_date=scheduled_date,
            completed_at=getattr(order, 'completed_date', None),  # Handle missing completed_date field
            patient_name=f"{patient.first_name} {patient.last_name}" if patient else "Unknown Patient",
            clinician_name=clinician.name if clinician else "Unknown Provider"
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to order test: {str(e)}"
        )

@router.get("/results/{order_id}", response_model=LabResultResponse)
async def get_results(
    order_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Get test results for a specific order
    """
    lab_service = LabService(db)
    
    # Check permission
    order = lab_service.order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if user has permission to access these results
    if (current_user.id != order.patient_id and  # Not the patient
        current_user.id != order.ordered_by and  # Not the ordering clinician (Fixed: use ordered_by)
        current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]):  # Not an admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these results"
        )
    
    try:
        results = lab_service.get_results(order_id)
        
        # Map DB status to schema status
        status_map = {
            DBResultStatus.PENDING: ResultStatus.PENDING_REVIEW,
            DBResultStatus.PRELIMINARY: ResultStatus.PENDING_REVIEW,
            DBResultStatus.FINAL: ResultStatus.NORMAL,
            DBResultStatus.AMENDED: ResultStatus.NORMAL,
            DBResultStatus.CANCELLED: ResultStatus.INCONCLUSIVE,
            DBResultStatus.CORRECTED: ResultStatus.NORMAL
        }
        
        result_status = ResultStatus.PENDING_REVIEW
        if results["status"] in status_map:
            result_status = status_map[results["status"]]
        
        # If marked as abnormal, override the status
        if results.get("abnormal", False):
            result_status = ResultStatus.ABNORMAL
        
        return LabResultResponse(
            result_id=results.get("result_id", order_id),
            order_id=order_id,
            result_summary=results.get("summary", "Results pending"),
            status=result_status,
            details=results.get("results", {}),
            images=results.get("images", []),
            notes=results.get("notes"),
            created_at=results.get("completed_at") or order.created_at,
            updated_at=results.get("completed_at") or order.updated_at
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve results: {str(e)}"
        )

@router.get("/patient/{patient_id}/orders", response_model=List[LabOrderResponse])
async def get_patient_orders(
    patient_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Get all lab orders for a patient
    """
    # Check permissions
    if (current_user.id != patient_id and  # Not the patient
        current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]):  # Not a clinician or admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these orders"
        )
    
    # If clinician, verify they are assigned to this patient
    if current_user.role == UserRole.CLINICIAN:
        # TODO: Add check to verify clinician is assigned to this patient
        pass
    
    lab_service = LabService(db)
    orders = lab_service.get_patient_orders(patient_id)
    
    # Convert to response format
    response_orders = []
    for order in orders:
        # Get patient and clinician names
        patient = lab_service.patient_repository.get_by_id(order.patient_id)
        clinician = lab_service.user_repository.get_by_id(order.ordered_by)  # Fixed: use ordered_by
        
        # Map DB status to schema status
        status_map = {
            DBOrderStatus.PENDING: OrderStatus.ORDERED,
            DBOrderStatus.APPROVED: OrderStatus.ORDERED,
            DBOrderStatus.COLLECTED: OrderStatus.SPECIMEN_COLLECTED,
            DBOrderStatus.IN_PROGRESS: OrderStatus.IN_PROCESS,
            DBOrderStatus.COMPLETED: OrderStatus.COMPLETED,
            DBOrderStatus.CANCELLED: OrderStatus.CANCELLED,
            DBOrderStatus.REJECTED: OrderStatus.REJECTED
        }
        
        order_status = OrderStatus.ORDERED
        if order.status in status_map:
            order_status = status_map[order.status]
        
        # Format scheduled date
        scheduled_date = None
        # Note: requisition_details field does not exist in current schema
        if False: # order.requisition_details and "scheduled_date" in order.requisition_details:
            from datetime import datetime
            try:
                scheduled_date = datetime.fromisoformat(order.requisition_details["scheduled_date"]).date()
            except (ValueError, TypeError):
                pass
        
        response_orders.append(LabOrderResponse(
            order_id=order.id,
            patient_id=order.patient_id,
            test_type=getattr(order, 'order_type', 'unknown'),
            clinician_id=order.ordered_by,
            notes=getattr(order, 'notes', ''),
            status=order_status,
            ordered_at=order.created_at,
            scheduled_date=scheduled_date,
            completed_at=getattr(order, 'completed_date', None),
            patient_name=f"{patient.first_name} {patient.last_name}" if patient else "Unknown Patient",
            clinician_name=clinician.name if clinician else "Unknown Provider"
        ))
    
    return response_orders

@router.get("/clinician/{clinician_id}/orders", response_model=List[LabOrderResponse])
async def get_clinician_orders(
    clinician_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Get all lab orders created by a clinician
    """
    # Check permissions
    if (current_user.id != clinician_id and  # Not the clinician
        current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]):  # Not an admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these orders"
        )
    
    lab_service = LabService(db)
    orders = lab_service.get_clinician_orders(clinician_id)
    
    # Convert to response format
    response_orders = []
    for order in orders:
        # Get patient and clinician names
        patient = lab_service.patient_repository.get_by_id(order.patient_id)
        clinician = lab_service.user_repository.get_by_id(order.ordered_by)  # Fixed: use ordered_by
        
        # Map DB status to schema status
        status_map = {
            DBOrderStatus.PENDING: OrderStatus.ORDERED,
            DBOrderStatus.APPROVED: OrderStatus.ORDERED,
            DBOrderStatus.COLLECTED: OrderStatus.SPECIMEN_COLLECTED,
            DBOrderStatus.IN_PROGRESS: OrderStatus.IN_PROCESS,
            DBOrderStatus.COMPLETED: OrderStatus.COMPLETED,
            DBOrderStatus.CANCELLED: OrderStatus.CANCELLED,
            DBOrderStatus.REJECTED: OrderStatus.REJECTED
        }
        
        order_status = OrderStatus.ORDERED
        if order.status in status_map:
            order_status = status_map[order.status]
        
        # Format scheduled date
        scheduled_date = None
        # Note: requisition_details field does not exist in current schema
        if False: # order.requisition_details and "scheduled_date" in order.requisition_details:
            from datetime import datetime
            try:
                scheduled_date = datetime.fromisoformat(order.requisition_details["scheduled_date"]).date()
            except (ValueError, TypeError):
                pass
        
        response_orders.append(LabOrderResponse(
            order_id=order.id,
            patient_id=order.patient_id,
            test_type=getattr(order, 'order_type', 'unknown'),
            clinician_id=order.ordered_by,
            notes=getattr(order, 'notes', ''),
            status=order_status,
            ordered_at=order.created_at,
            scheduled_date=scheduled_date,
            completed_at=getattr(order, 'completed_date', None),
            patient_name=f"{patient.first_name} {patient.last_name}" if patient else "Unknown Patient",
            clinician_name=clinician.name if clinician else "Unknown Provider"
        ))
    
    return response_orders

@router.post("/review_result/{result_id}", response_model=SuccessResponse)
async def review_result(
    result_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Mark a lab result as reviewed
    """
    # Only clinicians and admins can review results
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review lab results"
        )
    
    lab_service = LabService(db)
    
    # Get the result to check permissions
    result = lab_service.result_repository.get_by_id(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    # Get the order
    order = lab_service.order_repository.get_by_id(result.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if clinician is authorized to review this result
    if current_user.id != order.ordered_by and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:  # Fixed: use ordered_by
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this result"
        )
    
    try:
        lab_service.review_result(result_id, current_user.id)
        
        return SuccessResponse(
            message="Result marked as reviewed",
            data={"result_id": result_id}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review result: {str(e)}"
        )
