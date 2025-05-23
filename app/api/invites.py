from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.services.invites import InviteService
from app.services.users import UserService
from app.models.user import UserRole
from app.schemas.invites import (
    PatientInviteCreate, PatientInviteResponse, BulkInviteCreate, BulkInviteResponse,
    InviteResend, InviteVerification, InviteVerificationResponse, PatientRegistration,
    InviteStatus
)
from app.schemas.common import SuccessResponse
from datetime import datetime

router = APIRouter(prefix="/api", tags=["invites"])

@router.post("/generate_invite", response_model=PatientInviteResponse)
async def generate_invite(
    request: Request,
    patient_data: PatientInviteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a unique patient invite URL
    """
    # Only clinicians and admins can create invites
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create patient invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    invite_data = {
        "email": patient_data.email,
        "first_name": patient_data.first_name,
        "last_name": patient_data.last_name,
        "phone": patient_data.phone,
        "clinician_id": patient_data.provider_id or current_user.id,
        "custom_message": patient_data.custom_message
    }
    
    if hasattr(patient_data, "expiry_days") and patient_data.expiry_days:
        from datetime import timedelta
        invite_data["expires_at"] = datetime.utcnow() + timedelta(days=patient_data.expiry_days)
    
    try:
        invite = invite_service.create_invite(invite_data)
        
        # Generate an invite URL with the invite token
        base_url = str(request.base_url).rstrip("/")
        invite_url = invite_service.generate_invite_url(invite, base_url)
        
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        return PatientInviteResponse(
            invite_id=invite.id,
            email=invite.email,
            first_name=invite.first_name,
            last_name=invite.last_name,
            phone=invite.phone,
            invite_url=invite_url,
            provider_id=invite.clinician_id,
            provider_name=provider_name,
            status=InviteStatus(invite.status),
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            accepted_at=invite.accepted_at
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invite: {str(e)}"
        )

@router.post("/bulk_invite", response_model=BulkInviteResponse)
async def bulk_invite(
    request: Request,
    bulk_data: BulkInviteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple patient invites at once
    """
    # Only clinicians and admins can create invites
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create patient invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    # Process each invite in the bulk request
    invite_data_list = []
    for patient in bulk_data.patients:
        from datetime import timedelta
        
        invite_data = {
            "email": patient.email,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "phone": patient.phone,
            "clinician_id": patient.provider_id or current_user.id,
            "custom_message": patient.custom_message or bulk_data.custom_message,
            "expires_at": datetime.utcnow() + timedelta(days=patient.expiry_days)
        }
        invite_data_list.append(invite_data)
    
    # Create invites in bulk
    successful, failed = invite_service.create_bulk_invites(invite_data_list, current_user.id)
    
    # Convert successful invites to response format
    successful_responses = []
    base_url = str(request.base_url).rstrip("/")
    
    for invite in successful:
        # Generate an invite URL with the invite token
        invite_url = invite_service.generate_invite_url(invite, base_url)
        
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        successful_responses.append(PatientInviteResponse(
            invite_id=invite.id,
            email=invite.email,
            first_name=invite.first_name,
            last_name=invite.last_name,
            phone=invite.phone,
            invite_url=invite_url,
            provider_id=invite.clinician_id,
            provider_name=provider_name,
            status=InviteStatus(invite.status),
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            accepted_at=invite.accepted_at
        ))
    
    return BulkInviteResponse(
        successful=successful_responses,
        failed=failed,
        total_sent=len(successful_responses),
        total_failed=len(failed)
    )

@router.post("/resend_invite", response_model=PatientInviteResponse)
async def resend_invite(
    request: Request,
    resend_data: InviteResend,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Resend an expired or pending invite
    """
    # Only clinicians and admins can resend invites
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resend invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    try:
        invite = invite_service.resend_invite(resend_data.invite_id, resend_data.custom_message)
        
        # Generate an invite URL with the invite token
        base_url = str(request.base_url).rstrip("/")
        invite_url = invite_service.generate_invite_url(invite, base_url)
        
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        return PatientInviteResponse(
            invite_id=invite.id,
            email=invite.email,
            first_name=invite.first_name,
            last_name=invite.last_name,
            phone=invite.phone,
            invite_url=invite_url,
            provider_id=invite.clinician_id,
            provider_name=provider_name,
            status=InviteStatus(invite.status),
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            accepted_at=invite.accepted_at
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend invite: {str(e)}"
        )

@router.post("/verify_invite", response_model=InviteVerificationResponse)
async def verify_invite(
    verification: InviteVerification,
    db: Session = Depends(get_db)
):
    """
    Verify an invite token
    """
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    valid, invite, error_message = invite_service.verify_invite(verification.token)
    
    response = InviteVerificationResponse(
        valid=valid,
        error_message=error_message
    )
    
    if invite:
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        response.invite_id = invite.id
        response.patient_name = f"{invite.first_name} {invite.last_name}"
        response.provider_name = provider_name
        response.expires_at = invite.expires_at
    
    return response

@router.post("/register_patient", response_model=SuccessResponse)
async def register_patient(
    registration: PatientRegistration,
    db: Session = Depends(get_db)
):
    """
    Register a new patient from an invite
    """
    invite_service = InviteService(db)
    
    if not registration.agree_to_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must agree to the terms and conditions"
        )
    
    if registration.password != registration.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    user_data = {
        "password": registration.password,
        "date_of_birth": registration.date_of_birth
    }
    
    try:
        patient = invite_service.accept_invite(registration.invite_id, user_data)
        
        return SuccessResponse(
            message="Patient registered successfully",
            data={"patient_id": patient["user"].id}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register patient: {str(e)}"
        )

@router.get("/pending/{clinician_id}", response_model=List[PatientInviteResponse])
async def get_pending_invites(
    request: Request,
    clinician_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get pending invites for a clinician
    """
    # Check permissions
    if current_user.id != clinician_id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    invites = invite_service.get_invites_by_clinician(clinician_id, "pending")
    
    # Convert to response format
    responses = []
    base_url = str(request.base_url).rstrip("/")
    
    for invite in invites:
        # Generate an invite URL with the invite token
        invite_url = invite_service.generate_invite_url(invite, base_url)
        
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        responses.append(PatientInviteResponse(
            invite_id=invite.id,
            email=invite.email,
            first_name=invite.first_name,
            last_name=invite.last_name,
            phone=invite.phone,
            invite_url=invite_url,
            provider_id=invite.clinician_id,
            provider_name=provider_name,
            status=InviteStatus(invite.status),
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            accepted_at=invite.accepted_at
        ))
    
    return responses

@router.delete("/revoke/{invite_id}", response_model=SuccessResponse)
async def revoke_invite(
    invite_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a pending invite
    """
    invite_service = InviteService(db)
    
    # Get the invite to check permissions
    invite = invite_service.invite_repository.get_by_id(invite_id)
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    # Check permissions
    if invite.clinician_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this invite"
        )
    
    try:
        invite_service.revoke_invite(invite_id)
        
        return SuccessResponse(
            message="Invite revoked successfully",
            data={"invite_id": invite_id}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke invite: {str(e)}"
        )
    return PatientInviteResponse(
        invite_id=invite_id,
        invite_url=invite_url,
        email=patient_data.email,
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        phone=patient_data.phone,
        provider_id=patient_data.provider_id,
        provider_name="Provider Name",  # This should come from a service/database
        status="pending",
        created_at=datetime.now(),
        expires_at=datetime.now()  # This should be calculated properly
    )
