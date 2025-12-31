"""
Updated Eligibility API Endpoints

FastAPI routes for eligibility analysis that integrate with the new AI chat system.
This replaces the old eligibility.py that depended on the deprecated ChatService.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.api.auth import require_full_access, User
from app.services.ai_chat_engine import ChatEngineService
from app.repositories.ai_chat_repository import AIChatRepository
from app.services.eligibility import EligibilityService
from app.models.user import UserRole
from app.models.ai_chat import SessionStatus, SessionType
from app.schemas.eligibility import (
    EligibilityAssessmentRequest, EligibilityResult, 
    DetailedEligibilityResult, RiskFactor, PatientRecommendation,
    EligibilityParameters, EligibilitySummary
)

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])


@router.post("/analyze", response_model=EligibilityResult)
async def analyze_eligibility(
    assessment_req: EligibilityAssessmentRequest,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Analyze eligibility based on AI chat session data and risk factors.
    
    This endpoint integrates with the new AI chat system to extract
    patient information and perform eligibility analysis.
    """
    # Check authorization
    if assessment_req.patient_id != current_user.id and current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze eligibility for this patient"
        )
    
    # Initialize services
    ai_chat_repo = AIChatRepository(db)
    eligibility_service = EligibilityService(db)
    
    # Get the most recent AI chat session for this patient
    sessions = ai_chat_repo.get_sessions_by_patient(assessment_req.patient_id)
    
    if not sessions:
        # No chat sessions found, perform analysis based on available patient data
        analysis = eligibility_service.analyze_mock_eligibility(assessment_req.patient_id)
    else:
        # Use the most recent completed or active session
        session = sessions[0]  # Sessions should be ordered by creation date desc
        
        # Extract assessment data from the AI chat session
        chat_context = session.chat_context or {}
        extracted_data = session.extracted_data or {}
        assessment_results = session.assessment_results or {}
        
        # Perform eligibility analysis using chat data
        analysis = eligibility_service.analyze_mock_eligibility(assessment_req.patient_id)
        
        # Override with any session-specific data if available
        if "tyrer_cuzick_score" in assessment_results:
            analysis["tyrer_cuzick_score"] = assessment_results["tyrer_cuzick_score"]
        if "risk_factors" in extracted_data:
            analysis["risk_factors"] = extracted_data["risk_factors"]
    
    # Convert to response schema
    return EligibilityResult(
        is_eligible=analysis["is_eligible"],
        nccn_eligible=analysis["nccn_eligible"],
        tyrer_cuzick_score=analysis["tyrer_cuzick_score"],
        tyrer_cuzick_threshold=analysis["tyrer_cuzick_threshold"],
        risk_factors=analysis["risk_factors"],
        recommendations=analysis["recommendations"]
    )


@router.get("/analyze/{patient_id}", response_model=EligibilityResult)
async def get_patient_eligibility(
    patient_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Get the most recent eligibility assessment for a patient.
    
    This checks both stored eligibility results and AI chat session data.
    """
    # Check authorization
    if patient_id != current_user.id and current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view eligibility for this patient"
        )
    
    # Initialize services
    ai_chat_repo = AIChatRepository(db)
    eligibility_service = EligibilityService(db)
    
    # Get analysis from eligibility service
    analysis = eligibility_service.analyze_mock_eligibility(patient_id)
    
    # Try to enhance with AI chat session data
    sessions = ai_chat_repo.get_sessions_by_patient(patient_id)
    if sessions:
        session = sessions[0]
        assessment_results = session.assessment_results or {}
        
        # Use session data if available
        if "is_eligible" in assessment_results:
            analysis["is_eligible"] = assessment_results["is_eligible"]
        if "nccn_eligible" in assessment_results:
            analysis["nccn_eligible"] = assessment_results["nccn_eligible"]
    
    # Convert to response schema
    return EligibilityResult(
        is_eligible=analysis["is_eligible"],
        nccn_eligible=analysis["nccn_eligible"],
        tyrer_cuzick_score=analysis["tyrer_cuzick_score"],
        tyrer_cuzick_threshold=analysis["tyrer_cuzick_threshold"],
        risk_factors=analysis["risk_factors"],
        recommendations=analysis["recommendations"]
    )


@router.get("/detailed/{patient_id}", response_model=DetailedEligibilityResult)
async def get_detailed_eligibility(
    patient_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Get detailed eligibility information including risk factors and recommendations.
    
    Only available to clinicians and administrators.
    """
    # Check authorization - only clinicians and admins can see detailed results
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view detailed eligibility information"
        )
    
    # Initialize services
    ai_chat_repo = AIChatRepository(db)
    eligibility_service = EligibilityService(db)
    
    # Get detailed analysis
    analysis = eligibility_service.get_detailed_analysis(patient_id)
    
    # Try to enhance with AI chat session data
    session_id = None
    sessions = ai_chat_repo.get_sessions_by_patient(patient_id)
    if sessions:
        session = sessions[0]
        session_id = session.id
        
        # Merge with session data
        extracted_data = session.extracted_data or {}
        assessment_results = session.assessment_results or {}
        
        # Update analysis with session data
        analysis.update(assessment_results)
        if "risk_factors_detail" in extracted_data:
            analysis["risk_factors_detail"] = extracted_data["risk_factors_detail"]
    
    # Convert risk factors correctly - handle both string and dict formats
    risk_factor_enums = []
    risk_factors_detail = {}
    
    for rf in analysis.get("risk_factors", []):
        try:
            if isinstance(rf, str):
                # Simple string format from basic analysis
                risk_factor_enum = RiskFactor(rf)
                risk_factor_enums.append(risk_factor_enum)
                risk_factors_detail[risk_factor_enum.value] = {
                    "present": True,
                    "confidence": 0.8,
                    "description": f"Patient has {rf.replace('_', ' ')}"
                }
            elif isinstance(rf, dict) and "factor" in rf:
                # Dictionary format from detailed analysis
                risk_factor_enum = RiskFactor(rf["factor"])
                risk_factor_enums.append(risk_factor_enum)
                risk_factors_detail[risk_factor_enum.value] = {
                    "present": rf.get("present", True),
                    "confidence": 0.8,
                    "description": rf.get("details", f"Patient has {rf['factor'].replace('_', ' ')}")
                }
        except ValueError:
            # Skip invalid risk factors
            pass
    
    # Convert recommendations to strings (handle both string and dict formats)
    recommendations = []
    for rec in analysis.get("recommendations", []):
        if isinstance(rec, str):
            recommendations.append(rec)
        elif isinstance(rec, dict) and "description" in rec:
            recommendations.append(rec["description"])
        elif isinstance(rec, dict) and "type" in rec:
            # Fallback for dict format without description
            recommendations.append(f"{rec['type']}: {rec.get('description', 'See details')}")
    
    # Convert to detailed response schema  
    return DetailedEligibilityResult(
        is_eligible=analysis.get("is_eligible", False),
        nccn_eligible=analysis.get("nccn_eligible", False),
        tyrer_cuzick_score=analysis.get("tyrer_cuzick_score", 0.0),
        tyrer_cuzick_threshold=analysis.get("tyrer_cuzick_threshold", 0.2),
        risk_factors=risk_factor_enums,
        recommendations=recommendations,
        risk_factors_detail=risk_factors_detail,
        calculated_lifetime_risk=analysis.get("tyrer_cuzick_score", 0.0) * 100,  # Convert to percentage
        calculated_5year_risk=analysis.get("tyrer_cuzick_score", 0.0) * 20,  # Mock 5-year risk
        population_risk=5.0,  # Mock population baseline risk
        assessment_date=datetime.utcnow().isoformat()
    )


@router.post("/assess", response_model=DetailedEligibilityResult)
async def detailed_assessment(
    request: EligibilityAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Perform a detailed eligibility assessment for a patient.
    
    This endpoint can initiate a new AI chat session if needed
    and perform comprehensive eligibility analysis.
    """
    # Check authorization
    if request.patient_id != current_user.id and current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to assess eligibility for this patient"
        )
    
    # Initialize services
    ai_chat_repo = AIChatRepository(db)
    eligibility_service = EligibilityService(db)
    
    # Get detailed analysis
    analysis = eligibility_service.get_detailed_analysis(request.patient_id)
    
    # Try to get or create AI chat session for this patient
    sessions = ai_chat_repo.get_sessions_by_patient(request.patient_id)
    session_id = None
    
    if sessions:
        session = sessions[0]
        session_id = session.id
        
        # Update session with assessment results
        assessment_results = session.assessment_results or {}
        assessment_results.update({
            "is_eligible": analysis["is_eligible"],
            "nccn_eligible": analysis["nccn_eligible"],
            "assessment_date": datetime.utcnow().isoformat()
        })
        
        ai_chat_repo.update_session(session_id, {
            "assessment_results": assessment_results
        })
    
    # Mock detailed assessment data for demonstration
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
        assessment_date="2025-07-06",
        session_id=session_id,
        patient_id=request.patient_id,
        created_at=datetime.utcnow()
    )


@router.get("/recommendations/{patient_id}", response_model=List[PatientRecommendation])
async def get_patient_recommendations(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Get personalized recommendations for a patient based on their eligibility analysis.
    """
    # Check authorization
    if patient_id != current_user.id and current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view recommendations for this patient"
        )
    
    # In a real implementation, this would retrieve saved recommendations
    # from the database and AI chat session data
    
    # For now, return mock data
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


@router.get("/summary/{patient_id}", response_model=EligibilitySummary)
async def get_eligibility_summary(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Get a summary of eligibility status for a patient.
    """
    # Check authorization
    if patient_id != current_user.id and current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view eligibility summary for this patient"
        )
    
    # Initialize services
    ai_chat_repo = AIChatRepository(db)
    eligibility_service = EligibilityService(db)
    
    # Get basic analysis
    analysis = eligibility_service.analyze_mock_eligibility(patient_id)
    
    # Check if there are AI chat sessions
    sessions = ai_chat_repo.get_sessions_by_patient(patient_id)
    last_assessment_date = None
    
    if sessions:
        last_assessment_date = sessions[0].created_at.isoformat()
    else:
        last_assessment_date = "2025-07-06T00:00:00"  # Default date
    
    # Get patient name (for now use mock data, could fetch from user/patient repository)
    patient_name = f"Patient {patient_id[:8]}"
    
    # Extract primary risk factors
    primary_risk_factors = []
    if analysis.get("risk_factors"):
        primary_risk_factors = [factor for factor in analysis["risk_factors"][:3]]  # Top 3
    else:
        primary_risk_factors = ["family_history", "age"]  # Default mock data
    
    # Determine primary recommendation
    primary_recommendation = "Recommend regular screening"
    if analysis["is_eligible"]:
        if analysis["tyrer_cuzick_score"] > 0.2:
            primary_recommendation = "High-risk screening protocol recommended"
        else:
            primary_recommendation = "Standard screening protocol recommended"
    else:
        primary_recommendation = "Continue routine care"
    
    return EligibilitySummary(
        patient_id=patient_id,
        patient_name=patient_name,
        is_eligible=analysis["is_eligible"],
        assessment_date=last_assessment_date,
        primary_risk_factors=primary_risk_factors,
        primary_recommendation=primary_recommendation
    )
