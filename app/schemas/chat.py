"""
Pydantic schema models for chat and risk assessment related data transfer objects.

These schemas define the structure for request and response payloads
related to chat functionality and risk assessment calculations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime


class AnswerType(str, Enum):
    """Enumeration of possible answer types"""
    TEXT = "text"
    BOOLEAN = "boolean"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    DATE = "date"
    NUMBER = "number"


class RiskFactor(str, Enum):
    """Enumeration of known risk factors"""
    FAMILY_HISTORY = "FAMILY_HISTORY"
    AGE = "AGE"
    GENETIC_TESTING = "GENETIC_TESTING"
    PREVIOUS_BIOPSY = "PREVIOUS_BIOPSY"
    BREAST_DENSITY = "BREAST_DENSITY"
    HORMONE_REPLACEMENT = "HORMONE_REPLACEMENT"
    EARLY_MENARCHE = "EARLY_MENARCHE"
    LATE_MENOPAUSE = "LATE_MENOPAUSE"
    NULLIPARITY = "NULLIPARITY"
    LATE_FIRST_BIRTH = "LATE_FIRST_BIRTH"


class ChatQuestion(BaseModel):
    """Schema for basic chat question data"""
    id: str
    sequence: int
    text: str
    
    model_config = ConfigDict(from_attributes=True)


class ChatQuestionComplete(ChatQuestion):
    """Schema for complete chat question data including answer options"""
    description: Optional[str] = None
    answer_type: str = "text"
    options: Optional[List[str]] = None
    required: bool = True
    
    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Schema for chat responses"""
    sessionId: Optional[str] = None
    question: Optional[ChatQuestionComplete] = None
    nextQuestion: Optional[ChatQuestionComplete] = None
    sessionComplete: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class ChatSessionData(BaseModel):
    """Schema for chat session identification"""
    sessionId: Optional[str] = None
    patient_id: Optional[str] = None
    session_type: str = "assessment"
    
    model_config = ConfigDict(from_attributes=True)


class ChatAnswerData(BaseModel):
    """Schema for chat answer submission"""
    sessionId: str
    questionId: str
    answer: str
    answer_value: Optional[Union[str, int, float, List[str], Dict[str, Any]]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChatHistoryItem(BaseModel):
    """Schema for a single item in chat history"""
    question_id: str
    question_text: str
    answer_text: str
    answer_value: Optional[Any] = None
    timestamp: str
    
    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response"""
    history: List[ChatHistoryItem]
    
    model_config = ConfigDict(from_attributes=True)


class PatientRecommendation(BaseModel):
    """Schema for patient recommendations"""
    text: str
    priority: str = "medium"  # high, medium, low
    category: Optional[str] = None
    link: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EligibilityResult(BaseModel):
    """Schema for eligibility assessment results"""
    is_eligible: bool
    nccn_eligible: bool
    tyrer_cuzick_score: float
    tyrer_cuzick_threshold: float
    risk_factors: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True)


class DetailedEligibilityResult(EligibilityResult):
    """Schema for detailed eligibility assessment results"""
    session_id: str
    patient_id: str
    created_at: datetime
    risk_factors: List[RiskFactor]
    detailed_recommendations: List[PatientRecommendation]
    
    model_config = ConfigDict(from_attributes=True)


class EligibilityAssessmentRequest(BaseModel):
    """Schema for requesting a new eligibility assessment"""
    patient_id: str
    clinician_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
