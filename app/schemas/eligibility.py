"""
Pydantic schema models for eligibility-related data transfer objects.

These schemas define the structure for request and response payloads
related to patient eligibility assessment for screening programs.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class RiskFactor(str, Enum):
    """Enumeration of possible risk factors"""
    FAMILY_HISTORY = "family_history"
    PERSONAL_HISTORY = "personal_history"
    GENETIC_MUTATION = "genetic_mutation"
    AGE = "age"
    ETHNICITY = "ethnicity"
    RADIATION_EXPOSURE = "radiation_exposure"
    HORMONE_REPLACEMENT = "hormone_replacement"
    REPRODUCTIVE_HISTORY = "reproductive_history"
    LIFESTYLE = "lifestyle"
    BREAST_DENSITY = "breast_density"
    OTHER = "other"


class RecommendationType(str, Enum):
    """Enumeration of possible recommendation types"""
    SCREENING = "screening"
    GENETIC_TESTING = "genetic_testing"
    CLINICAL_EXAM = "clinical_exam"
    SPECIALIST_REFERRAL = "specialist_referral"
    LIFESTYLE_CHANGE = "lifestyle_change"
    RISK_REDUCING_MEDICATION = "risk_reducing_medication"
    SURGICAL_CONSULTATION = "surgical_consultation"
    NO_RECOMMENDATION = "no_recommendation"


class EligibilityResult(BaseModel):
    """Schema for eligibility assessment results"""
    is_eligible: bool
    nccn_eligible: bool
    tyrer_cuzick_score: float
    tyrer_cuzick_threshold: float
    risk_factors: Optional[List[RiskFactor]] = None
    recommendations: Optional[List[str]] = None


class DetailedEligibilityResult(EligibilityResult):
    """Schema for detailed eligibility results"""
    risk_factors_detail: Dict[str, Any] = Field(default_factory=dict)
    calculated_lifetime_risk: float
    calculated_5year_risk: float
    population_risk: float
    assessment_date: str  # ISO format date


class EligibilityParameters(BaseModel):
    """Schema for customizing eligibility calculation parameters"""
    nccn_threshold: Optional[float] = None
    tyrer_cuzick_threshold: Optional[float] = None
    include_ashkenazi_jewish: bool = True
    include_personal_history: bool = True
    max_age: Optional[int] = None


class EligibilityAssessmentRequest(BaseModel):
    """Schema for requesting eligibility assessment for a patient"""
    patient_id: str
    session_id: Optional[str] = None
    parameters: Optional[EligibilityParameters] = None


class RecommendationBase(BaseModel):
    """Base schema for recommendations"""
    type: RecommendationType
    description: str
    frequency: Optional[str] = None
    start_age: Optional[int] = None
    supporting_evidence: Optional[str] = None


class PatientRecommendation(RecommendationBase):
    """Schema for patient-specific recommendations"""
    id: str
    patient_id: str
    priority: int = 1  # 1=highest priority
    completed: bool = False
    due_date: Optional[str] = None  # ISO format date


class EligibilitySummary(BaseModel):
    """Schema for eligibility summary data"""
    patient_id: str
    patient_name: str
    is_eligible: bool
    assessment_date: str  # ISO format date
    primary_risk_factors: List[str]
    primary_recommendation: str

