from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.services.chat import ChatService
from app.models.user import UserRole
from app.schemas.chat import (
    EligibilityAssessmentRequest, EligibilityResult, 
    DetailedEligibilityResult, RiskFactor, PatientRecommendation
)

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])

@router.post("/analyze", response_model=EligibilityResult)
async def analyze_eligibility(
    assessment_req: EligibilityAssessmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze eligibility based on chat answers and risk factors
    """
    # Check authorization
    if assessment_req.patient_id != current_user.id and current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze eligibility for this patient"
        )
    
    # If clinician, verify they are assigned to this patient
    if current_user.role == UserRole.CLINICIAN:
        # TODO: Add check to verify clinician is assigned to this patient
        pass
    
    chat_service = ChatService(db)
    
    # Get the most recent active session for this patient
    session = chat_service.session_repository.get_active_session_by_patient(assessment_req.patient_id)
    
    if not session:
        # No active session found, look for completed sessions
        sessions = chat_service.session_repository.get_sessions_by_patient(assessment_req.patient_id)
        if sessions:
            session = sessions[0]  # Get the most recent session
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chat sessions found for this patient"
            )
    
    # Get or calculate risk assessment
    assessment = chat_service.get_or_calculate_risk_assessment(session.id)
    
    # Convert to response schema
    return EligibilityResult(
        is_eligible=assessment.is_eligible,
        nccn_eligible=assessment.nccn_eligible,
        tyrer_cuzick_score=assessment.tyrer_cuzick_score,
        tyrer_cuzick_threshold=assessment.tyrer_cuzick_threshold,
        risk_factors=assessment.risk_factors,
        recommendations=assessment.recommendations
    )

@router.get("/analyze/{patient_id}", response_model=EligibilityResult)
async def get_patient_eligibility(
    patient_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the most recent eligibility assessment for a patient
    """
    # Check authorization
    if patient_id != current_user.id and current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view eligibility for this patient"
        )
    
    # If clinician, verify they are assigned to this patient
    if current_user.role == UserRole.CLINICIAN:
        # TODO: Add check to verify clinician is assigned to this patient
        pass
    
    chat_service = ChatService(db)
    
    # Get the most recent risk assessment
    assessment = chat_service.risk_repository.get_latest_by_patient(patient_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No eligibility assessment found for this patient"
        )
    
    # Convert to response schema
    return EligibilityResult(
        is_eligible=assessment.is_eligible,
        nccn_eligible=assessment.nccn_eligible,
        tyrer_cuzick_score=assessment.tyrer_cuzick_score,
        tyrer_cuzick_threshold=assessment.tyrer_cuzick_threshold,
        risk_factors=assessment.risk_factors,
        recommendations=assessment.recommendations
    )

@router.get("/detailed/{patient_id}", response_model=DetailedEligibilityResult)
async def get_detailed_eligibility(
    patient_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed eligibility information including risk factors and recommendations
    """
    # Check authorization - only clinicians and admins can see detailed results
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view detailed eligibility information"
        )
    
    # If clinician, verify they are assigned to this patient
    if current_user.role == UserRole.CLINICIAN:
        # TODO: Add check to verify clinician is assigned to this patient
        pass
    
    chat_service = ChatService(db)
    
    # Get the most recent risk assessment
    assessment = chat_service.risk_repository.get_latest_by_patient(patient_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No eligibility assessment found for this patient"
        )
    
    # Convert string risk factors to enum types
    risk_factor_enums = []
    for rf in assessment.risk_factors:
        try:
            risk_factor_enums.append(RiskFactor(rf))
        except ValueError:
            # Skip invalid risk factors
            pass
    
    # Create detailed recommendations
    detailed_recommendations = []
    for rec in assessment.recommendations:
        detailed_recommendations.append(
            PatientRecommendation(
                text=rec,
                priority="high" if "recommend" in rec.lower() else "medium",
                category="screening"
            )
        )
    
    # Convert to detailed response schema
    return DetailedEligibilityResult(
        is_eligible=assessment.is_eligible,
        nccn_eligible=assessment.nccn_eligible,
        tyrer_cuzick_score=assessment.tyrer_cuzick_score,
        tyrer_cuzick_threshold=assessment.tyrer_cuzick_threshold,
        risk_factors=risk_factor_enums,
        recommendations=assessment.recommendations,
        detailed_recommendations=detailed_recommendations,
        session_id=assessment.session_id,
        patient_id=assessment.patient_id,
        created_at=assessment.created_at
    )
    
    
@router.post("/assess", response_model=DetailedEligibilityResult)
async def detailed_assessment(
    request: EligibilityAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform a detailed eligibility assessment for a patient
    """
    # In a real implementation, this would:
    # 1. Retrieve the patient's health information
    # 2. Run a comprehensive risk assessment algorithm
    # 3. Save the results to the database
    
    # For demo purposes, we'll just return mock data
    return DetailedEligibilityResult(
        is_eligible=True,
        nccn_eligible=True,
        tyrer_cuzick_score=8.5,
        tyrer_cuzick_threshold=7.5,
        risk_factors=[RiskFactor.FAMILY_HISTORY, RiskFactor.AGE, RiskFactor.BREAST_DENSITY],
        recommendations=["Annual mammogram recommended", "Consider genetic testing"],
        risk_factors_detail={
            "family_history": {
                "first_degree_relatives": 1,
                "age_at_diagnosis": 45
            },
            "breast_density": "heterogeneously dense"
        },
        calculated_lifetime_risk=23.5,
        calculated_5year_risk=3.2,
        population_risk=12.5,
        assessment_date="2025-05-12"
    )


@router.get("/recommendations/{patient_id}", response_model=List[PatientRecommendation])
async def get_patient_recommendations(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get personalized recommendations for a patient
    """
    # In a real implementation, this would retrieve saved recommendations
    # from the database
    
    # For demo purposes, we'll just return mock data
    return [
        PatientRecommendation(
            id="rec1",
            patient_id=patient_id,
            type="screening",
            description="Annual mammogram",
            frequency="yearly",
            start_age=40,
            priority=1,
            supporting_evidence="NCCN guidelines for high-risk patients",
            due_date="2025-06-15"
        ),
        PatientRecommendation(
            id="rec2",
            patient_id=patient_id,
            type="genetic_testing",
            description="BRCA1/2 genetic testing",
            priority=2,
            supporting_evidence="Family history indicates potential hereditary risk",
        )
    ]
