from fastapi import APIRouter, HTTPException
from app.schemas import ChatSessionData, EligibilityResult

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
        tyrer_cuzick_threshold=7.5
    )
