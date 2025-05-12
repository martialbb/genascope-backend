from pydantic import BaseModel
from typing import Optional

class ChatQuestion(BaseModel):
    id: int
    text: str

class ChatResponse(BaseModel):
    question: Optional[ChatQuestion] = None
    nextQuestion: Optional[ChatQuestion] = None

class ChatSessionData(BaseModel):
    sessionId: str

class ChatAnswerData(BaseModel):
    sessionId: str
    questionId: int
    answer: str

class EligibilityResult(BaseModel):
    is_eligible: bool
    nccn_eligible: bool
    tyrer_cuzick_score: float
    tyrer_cuzick_threshold: float
