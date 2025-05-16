"""
Pydantic schema models for chat and risk assessment related data transfer objects.

These schemas define the structure for request and response payloads
related to chat functionality and risk assessment calculations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ChatQuestion(BaseModel):
    """Schema for chat question data"""
    id: int
    text: str


class ChatResponse(BaseModel):
    """Schema for chat responses"""
    question: Optional[ChatQuestion] = None
    nextQuestion: Optional[ChatQuestion] = None


class ChatSessionData(BaseModel):
    """Schema for chat session identification"""
    sessionId: str


class AnswerType(str, Enum):
    """Enumeration of possible answer types"""
    TEXT = "text"
    BOOLEAN = "boolean"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    DATE = "date"
    NUMBER = "number"


class ChatQuestionComplete(ChatQuestion):
    """Schema for complete chat question data including answer options"""
    answer_type: AnswerType = AnswerType.TEXT
    options: Optional[List[str]] = None
    required: bool = True
    description: Optional[str] = None


class ChatAnswerData(BaseModel):
    """Schema for chat answer submission"""
    sessionId: str
    questionId: int
    answer: str


class EligibilityResult(BaseModel):
    """Schema for eligibility assessment results"""
    is_eligible: bool
    nccn_eligible: bool
    tyrer_cuzick_score: float
    tyrer_cuzick_threshold: float
    risk_factors: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
