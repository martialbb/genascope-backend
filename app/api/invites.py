from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import traceback
from datetime import datetime, timedelta
from app.db.database import get_db
from app.api.auth import get_current_active_user, User, create_access_token
from app.services.invites import InviteService
from app.services.users import UserService
from app.services.patients import PatientService
from app.models.user import UserRole
from app.schemas.invites import (
    PatientInviteCreate, PatientInviteResponse, BulkInviteCreate, BulkInviteResponse,
    InviteResend, InviteVerification, InviteVerificationResponse, PatientRegistration,
    InviteStatus, InviteListResponse, InviteListParams, SimplifiedPatientAccess, SimplifiedAccessResponse
)
from app.schemas.users import UserResponse
from app.schemas.common import SuccessResponse
from datetime import datetime

router = APIRouter(prefix="/api", tags=["invites"])

@router.post("/generate_invite", response_model=PatientInviteResponse)
async def generate_invite(
    request: Request,
    invite_data: PatientInviteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a unique patient invite URL
    
    This endpoint now requires a pre-created patient_id
    """
    # Only clinicians and admins can create invites
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create patient invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    patient_service = PatientService(db)
    
    # Use provided provider_id or fall back to current user
    provider_id = invite_data.provider_id if invite_data.provider_id else current_user.id
    
    # Debug logging
    print(f"DEBUG: generate_invite called by user {current_user.id} ({current_user.role})")
    print(f"DEBUG: provider_id from request: {invite_data.provider_id}")
    print(f"DEBUG: using provider_id: {provider_id}")
    print(f"DEBUG: patient_id from request: {invite_data.patient_id}")
    
    # Validate the provider exists and has appropriate role
    provider = user_service.get_user_by_id(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with ID {provider_id} not found"
        )
    
    if provider.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {provider.name} (role: {provider.role}) cannot be assigned as a provider. Only clinicians, admins, and super admins can be providers."
        )
    
    # Get patient data to verify it exists
    try:
        patient_data = patient_service.get_patient_with_invite_status(invite_data.patient_id)
        
        # Note: We no longer block multiple invites here since patients can have 
        # multiple invites with different chat strategies
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {invite_data.patient_id} not found"
            )
        raise e
    
    # Create invitation data
    invite_creation_data = {
        "patient_id": invite_data.patient_id,
        "email": patient_data["email"],  # Use email from patient record
        "clinician_id": provider_id,
        "chat_strategy_id": invite_data.chat_strategy_id,
        "custom_message": invite_data.custom_message
    }
    
    if invite_data.expiry_days:
        from datetime import timedelta
        invite_creation_data["expires_at"] = datetime.utcnow() + timedelta(days=invite_data.expiry_days)
    
    # Store send_email separately for service logic - don't pass to PatientInvite model
    send_email = invite_data.send_email if invite_data.send_email is not None else True
    invite_creation_data["send_email"] = send_email
        
    try:
        print(f"DEBUG: Calling create_invite with data: {invite_creation_data}")
        invite = invite_service.create_invite(invite_creation_data)
        print(f"DEBUG: Invite created successfully with ID: {invite.id} and token: {invite.invite_token}")
        
        # Generate an invite URL with the invite token using the frontend URL from settings
        invite_url = invite_service.generate_invite_url(invite)
        print(f"DEBUG: Generated invite URL: {invite_url}")
        
        # Get provider name
        provider_name = provider.name
        
        return PatientInviteResponse(
            invite_id=str(invite.id),
            email=invite.email,
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            phone=patient_data["phone"],
            invite_url=invite_url,
            provider_id=invite.clinician_id,
            provider_name=provider_name,
            status=InviteStatus(invite.status),
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            accepted_at=invite.accepted_at
        )
    except HTTPException as e:
        print(f"DEBUG: HTTPException in generate_invite: {e.detail}")
        raise e
    except Exception as e:
        print(f"ERROR: Failed to create invite: {str(e)}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
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
    patient_service = PatientService(db)
    
    # Process each invite in the bulk request
    invite_data_list = []
    failed_invites = []
    
    for patient_invite in bulk_data.patients:
        from datetime import timedelta
        
        try:
            # Get patient data to verify it exists
            patient_data = patient_service.get_patient_with_invite_status(patient_invite.patient_id)
            
            # Note: We no longer skip patients with pending invites here since patients 
            # can have multiple invites with different chat strategies
                
            # Create invitation data
            invite_data = {
                "patient_id": patient_invite.patient_id,
                "email": patient_data["email"],
                "first_name": patient_data["first_name"],
                "last_name": patient_data["last_name"],
                "phone": patient_data["phone"],
                "clinician_id": patient_invite.provider_id or current_user.id,
                "chat_strategy_id": patient_invite.chat_strategy_id or bulk_data.default_chat_strategy_id,
                "custom_message": patient_invite.custom_message or bulk_data.custom_message,
                "expires_at": datetime.utcnow() + timedelta(days=patient_invite.expiry_days)
            }
            
            # Validate that chat_strategy_id is provided
            if not invite_data["chat_strategy_id"]:
                failed_invites.append({
                    "data": {"patient_id": patient_invite.patient_id},
                    "error": "chat_strategy_id is required either per patient or as default_chat_strategy_id"
                })
                continue
            invite_data_list.append(invite_data)
        except HTTPException as e:
            failed_invites.append({
                "data": {"patient_id": patient_invite.patient_id},
                "error": str(e.detail)
            })
        except Exception as e:
            failed_invites.append({
                "data": {"patient_id": patient_invite.patient_id},
                "error": str(e)
            })
    
    # Create invites in bulk
    successful, creation_failed = invite_service.create_bulk_invites(invite_data_list, current_user.id)
    
    # Combine pre-check failures with creation failures
    failed = failed_invites + creation_failed
    
    # Convert successful invites to response format
    successful_responses = []
    
    for invite in successful:
        # Generate an invite URL with the invite token using frontend URL
        invite_url = invite_service.generate_invite_url(invite)
        
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        successful_responses.append(PatientInviteResponse(
            invite_id=str(invite.id),
            email=invite.email,
            first_name=invite.patient.first_name if invite.patient else "",
            last_name=invite.patient.last_name if invite.patient else "",
            phone=invite.patient.phone if invite.patient else None,
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
    
    # Get the invite first to check permissions
    invite = invite_service.get_invite_by_id(resend_data.invite_id)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    # Check account-based permissions
    if current_user.role == UserRole.CLINICIAN:
        # Clinicians can only resend their own invites
        if invite.clinician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to resend this invite"
            )
    elif current_user.role == UserRole.ADMIN:
        # Admins can only resend invites for patients in their account
        if invite.patient and invite.patient.account_id != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to resend this invite"
            )
    # Super admins can resend any invite
    
    try:
        invite = invite_service.resend_invite(resend_data.invite_id, resend_data.custom_message)
        
        # Generate an invite URL with the invite token using frontend URL
        invite_url = invite_service.generate_invite_url(invite)
        
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        return PatientInviteResponse(
            invite_id=str(invite.id),
            email=invite.email,
            first_name=invite.patient.first_name if invite.patient else "",
            last_name=invite.patient.last_name if invite.patient else "",
            phone=invite.patient.phone if invite.patient else None,
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
        response.patient_name = invite.patient.full_name if invite.patient else "Patient"
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

@router.post("/simplified_access", response_model=SimplifiedAccessResponse)
async def simplified_patient_access(
    access_data: SimplifiedPatientAccess,
    db: Session = Depends(get_db)
):
    """
    Simplified patient access using basic information only.
    Patients can access chat interface with first name, last name, date of birth,
    and agreement to terms & privacy policy - no password required.
    """
    invite_service = InviteService(db)
    patient_service = PatientService(db)
    
    try:
        # Verify the invite token first
        valid, invite, error_message = invite_service.verify_invite(access_data.invite_token)
        
        if not valid or not invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message or "Invalid or expired invite"
            )
        
        # Get the patient associated with this invite
        if not invite.patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No patient associated with this invite"
            )
        
        patient = invite.patient
        
        # Verify patient information matches
        if (patient.first_name.lower() != access_data.first_name.lower() or
            patient.last_name.lower() != access_data.last_name.lower()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient information does not match"
            )
        
        # Verify date of birth if patient has one
        if patient.date_of_birth:
            patient_dob_str = patient.date_of_birth.strftime("%Y-%m-%d")
            if patient_dob_str != access_data.date_of_birth:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Date of birth does not match"
                )
        
        # Mark the invite as accessed (but not fully accepted like password registration)
        # Create a temporary access session
        invite_service.mark_invite_accessed(invite.id)
        
        # Generate JWT token for simplified access
        # Use a shorter expiration time for simplified access (4 hours instead of 24)
        token_data = {
            "sub": patient.id,  # Use patient ID as subject, not email
            "email": patient.email,  # Keep email separate for reference
            "id": patient.id,
            "role": "patient",
            "access_type": "simplified",  # Mark this as simplified access
            "invite_id": invite.id
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=4)  # Shorter session for simplified access
        )
        
        return SimplifiedAccessResponse(
            access_token=access_token,
            token_type="bearer",
            patient_id=patient.id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            expires_in=14400  # 4 hours in seconds
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in simplified_access: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate patient: {str(e)}"
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
    from app.services.users import UserService
    
    user_service = UserService(db)
    
    # Check role-based permissions
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admins can view any clinician's invites
        pass
    elif current_user.role == UserRole.ADMIN:
        # Regular admins can only view invites for clinicians in their account
        if not current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not associated with any organization"
            )
        
        # Verify the target clinician belongs to the same account
        target_clinician = user_service.get_user_by_id(clinician_id)
        if not target_clinician or target_clinician.account_id != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these invites"
            )
    elif current_user.role == UserRole.CLINICIAN:
        # Clinicians can only view their own invites
        if current_user.id != clinician_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these invites"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    invites = invite_service.get_invites_by_clinician(clinician_id, "pending")
    
    # Convert to response format
    responses = []
    
    for invite in invites:
        # Generate an invite URL with the invite token using frontend URL
        invite_url = invite_service.generate_invite_url(invite)
        
        # Get provider name
        provider = user_service.get_user_by_id(invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        responses.append(PatientInviteResponse(
            invite_id=str(invite.id),
            email=invite.email,
            first_name=invite.patient.first_name if invite.patient else "",
            last_name=invite.patient.last_name if invite.patient else "",
            phone=invite.patient.phone if invite.patient else None,
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
    if current_user.role == UserRole.CLINICIAN:
        # Clinicians can only revoke their own invites
        if invite.clinician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revoke this invite"
            )
    elif current_user.role == UserRole.ADMIN:
        # Admins can only revoke invites for patients in their account
        if invite.patient and invite.patient.account_id != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revoke this invite"
            )
    # Super admins can revoke any invite
    
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

@router.get("/invites", response_model=InviteListResponse)
async def list_invites(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    clinician_id: Optional[str] = Query(None, description="Filter by clinician"),
    search: Optional[str] = Query(None, description="Search by patient name or email"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List invites with filtering, pagination, and sorting
    """
    # Check permissions - only clinicians and admins can view invites
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    # Build filter parameters
    filters = {}
    if status and status in [s.value for s in InviteStatus]:
        filters["status"] = status
    
    # Apply role-based access control for account filtering
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admins can see all invites across all accounts
        if clinician_id:
            filters["clinician_id"] = clinician_id
    else:
        # Regular admins and clinicians can only see invites from their account
        if not current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not associated with any organization"
            )
        
        # Add account filtering for non-super admins
        filters["account_id"] = current_user.account_id
        
        # If user is clinician, only show their invites
        if current_user.role == UserRole.CLINICIAN:
            filters["clinician_id"] = current_user.id
        elif clinician_id:
            filters["clinician_id"] = clinician_id
    
    if search:
        filters["search"] = search
    
    # Get paginated invites
    invites, total_count = invite_service.list_invites_paginated(
        page=page,
        limit=limit,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Convert to response format
    invite_responses = []
    for invite in invites:
        # Generate invite URL
        invite_url = invite_service.generate_invite_url(invite)
        
        # Get provider name
        if invite.clinician_id:
            provider = user_service.get_user_by_id(invite.clinician_id)
            provider_name = provider.name if provider else "Unknown Provider"
        else:
            provider_name = "No Provider Assigned"
        
        invite_responses.append(PatientInviteResponse(
            invite_id=str(invite.id),
            email=invite.email,
            first_name=invite.patient.first_name if invite.patient else "",
            last_name=invite.patient.last_name if invite.patient else "",
            phone=invite.patient.phone if invite.patient else None,
            invite_url=invite_url,
            provider_id=invite.clinician_id or "",  # Use empty string if None
            provider_name=provider_name,
            status=InviteStatus(invite.status),
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            accepted_at=invite.accepted_at
        ))
    
    # Calculate pagination metadata
    total_pages = (total_count + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    return InviteListResponse(
        invites=invite_responses,
        total_count=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/invites/{invite_id}", response_model=PatientInviteResponse)
async def get_invite_details(
    invite_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get specific invite details
    """
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    # Get the invite
    invite = invite_service.get_invite_by_id(invite_id)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    # Check role-based permissions
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admins can view all invites
        pass
    elif current_user.role == UserRole.ADMIN:
        # Regular admins can only view invites from their account
        if not current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not associated with any organization"
            )
        
        # Verify the invite's patient belongs to the admin's account
        if invite.patient and invite.patient.account_id != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this invite"
            )
    elif current_user.role == UserRole.CLINICIAN:
        # Clinicians can only view their own invites within their account
        if invite.clinician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this invite"
            )
        
        # Additional account verification for clinicians
        if not current_user.account_id or (invite.patient and invite.patient.account_id != current_user.account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this invite"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invites"
        )
    
    # Generate invite URL
    invite_url = invite_service.generate_invite_url(invite)
    
    # Get provider name
    provider = user_service.get_user_by_id(invite.clinician_id)
    provider_name = provider.name if provider else "Unknown Provider"
    
    return PatientInviteResponse(
        invite_id=str(invite.id),
        email=invite.email,
        first_name=invite.patient.first_name if invite.patient else "",
        last_name=invite.patient.last_name if invite.patient else "",
        phone=invite.patient.phone if invite.patient else None,
        invite_url=invite_url,
        provider_id=invite.clinician_id,
        provider_name=provider_name,
        status=InviteStatus(invite.status),
        created_at=invite.created_at,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at
    )

@router.post("/invites/{invite_id}/resend", response_model=PatientInviteResponse)
async def resend_specific_invite(
    invite_id: str,
    custom_message: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Resend a specific invite
    """
    # Only clinicians and admins can resend invites
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resend invites"
        )
    
    invite_service = InviteService(db)
    user_service = UserService(db)
    
    # Get the invite first to check permissions
    invite = invite_service.get_invite_by_id(invite_id)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.CLINICIAN:
        # Clinicians can only resend their own invites
        if invite.clinician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to resend this invite"
            )
    elif current_user.role == UserRole.ADMIN:
        # Admins can only resend invites for patients in their account
        if invite.patient and invite.patient.account_id != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to resend this invite"
            )
    # Super admins can resend any invite
    
    try:
        updated_invite = invite_service.resend_invite(invite_id, custom_message)
        
        # Generate invite URL
        invite_url = invite_service.generate_invite_url(updated_invite)
        
        # Get provider name
        provider = user_service.get_user_by_id(updated_invite.clinician_id)
        provider_name = provider.name if provider else "Unknown Provider"
        
        return PatientInviteResponse(
            invite_id=str(updated_invite.id),
            email=updated_invite.email,
            first_name=updated_invite.patient.first_name if updated_invite.patient else "",
            last_name=updated_invite.patient.last_name if updated_invite.patient else "",
            phone=updated_invite.patient.phone if updated_invite.patient else None,
            invite_url=invite_url,
            provider_id=updated_invite.clinician_id,
            provider_name=provider_name,
            status=InviteStatus(updated_invite.status),
            created_at=updated_invite.created_at,
            expires_at=updated_invite.expires_at,
            accepted_at=updated_invite.accepted_at
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend invite: {str(e)}"
        )

@router.get("/patients/{patient_id}/invites", response_model=List[PatientInviteResponse])
async def get_patient_invites(
    patient_id: str,
    invite_status: Optional[str] = Query(None, alias="status", description="Filter by invite status: pending, accepted, expired, revoked"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all invites for a specific patient
    
    This endpoint allows authorized users to view all invitation history for a patient,
    optionally filtered by status. Useful for tracking patient engagement and invite management.
    """
    invite_service = InviteService(db)
    patient_service = PatientService(db)
    user_service = UserService(db)
    
    # Verify patient exists first
    try:
        patient_data = patient_service.get_patient_with_invite_status(patient_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        raise e
    
    # Check role-based permissions
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admins can view all patient invites
        pass
    elif current_user.role == UserRole.ADMIN:
        # Regular admins can only view invites for patients in their account
        if not current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not associated with any organization"
            )
        
        # Verify the patient belongs to the admin's account
        if patient_data.get("account_id") != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view invites for patients outside your organization"
            )
    elif current_user.role == UserRole.CLINICIAN:
        # Clinicians can view invites for their assigned patients
        if patient_data.get("clinician_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view invites for patients not assigned to you"
            )
    elif current_user.role == UserRole.PATIENT and current_user.is_simplified_access:
        # Simplified access patients can only view their own invites
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view other patients' invites"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view patient invites"
        )
    
    # Get invites for the patient
    try:
        invites = invite_service.get_invites_by_patient(patient_id, invite_status)
        
        # Convert to response format
        invite_responses = []
        
        for invite in invites:
            # Generate invite URL
            invite_url = invite_service.generate_invite_url(invite)
            
            # Get provider name
            provider = user_service.get_user_by_id(invite.clinician_id)
            provider_name = provider.name if provider else "Unknown Provider"
            
            invite_responses.append(PatientInviteResponse(
                invite_id=str(invite.id),
                email=invite.email,
                first_name=invite.patient.first_name if invite.patient else "",
                last_name=invite.patient.last_name if invite.patient else "",
                phone=invite.patient.phone if invite.patient else None,
                invite_url=invite_url,
                provider_id=invite.clinician_id,
                provider_name=provider_name,
                status=InviteStatus(invite.status),
                created_at=invite.created_at,
                expires_at=invite.expires_at,
                accepted_at=invite.accepted_at
            ))
        
        return invite_responses
        
    except Exception as e:
        print(f"Error getting patient invites: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient invites: {str(e)}"
        )

@router.get("/clinicians", response_model=List[UserResponse])
async def list_clinicians(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List available clinicians/providers for invite assignment
    """
    # Only clinicians and admins can view clinician list
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view clinicians"
        )
    
    user_service = UserService(db)
    
    # Apply role-based access control for clinicians list
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admins can see all active clinicians
        clinicians = user_service.get_users_by_role([UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN])
    else:
        # Regular admins and clinicians can only see clinicians from their account
        if not current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not associated with any organization"
            )
        
        # Get clinicians from the same account only
        clinicians = user_service.get_users_by_role_and_account(
            roles=[UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN],
            account_id=current_user.account_id
        )
    
    # Convert to response format
    clinician_responses = []
    for clinician in clinicians:
        if clinician.is_active:  # Only include active clinicians
            clinician_responses.append(UserResponse(
                id=clinician.id,
                email=clinician.email,
                name=clinician.name,
                role=clinician.role,
                is_active=clinician.is_active,
                created_at=clinician.created_at
            ))
    
    return clinician_responses
