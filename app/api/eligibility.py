from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.schemas import (
    ChatSessionData, EligibilityResult, EligibilityAssessmentRequest,
    DetailedEligibilityResult, RiskFactor, PatientRecommendation
)

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])

@router.post("/analyze", response_model=EligibilityResult)
async def analyze_eligibility(session_data: ChatSessionData):
    """
    Analyze eligibility based on chat answers
    """
    session_id = session_data.sessionId
    
    # In a real implementation, this would fetch chat answers from a database
    # and run a risk assessment algorithm
    
    # For demo purposes, we'll just return mock data
    return EligibilityResult(
        is_eligible=True,
        nccn_eligible=True,
        tyrer_cuzick_score=8.5,
        tyrer_cuzick_threshold=7.5,
        risk_factors=[RiskFactor.FAMILY_HISTORY, RiskFactor.AGE],
        recommendations=["Annual mammogram recommended", "Consider genetic testing"]
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
