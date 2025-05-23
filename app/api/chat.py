from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.services.chat import ChatService
from app.schemas.chat import (
    ChatQuestion, ChatResponse, ChatSessionData, ChatAnswerData, 
    ChatQuestionComplete, EligibilityResult
)
from app.models.user import UserRole
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/start_chat", response_model=ChatResponse)
async def start_chat(
    session_data: ChatSessionData,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start a new chat session or resume an existing one
    """
    # Only patients and clinicians can start chats
    if current_user.role not in [UserRole.PATIENT, UserRole.CLINICIAN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to start chat sessions"
        )
    
    chat_service = ChatService(db)
    
    # If clinician, they need to specify a patient_id in the session data
    patient_id = current_user.id  # Default to current user (for patients)
    
    if current_user.role in [UserRole.CLINICIAN, UserRole.ADMIN]:
        # Clinicians must specify a patient
        if not session_data.patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient ID required for clinician-initiated chats"
            )
        patient_id = session_data.patient_id
    
    # Create or get existing session
    session = chat_service.get_or_create_session(
        patient_id, 
        {"session_type": session_data.session_type if hasattr(session_data, "session_type") else "assessment"}
    )
    
    # Get the first/next question
    next_question = chat_service.get_next_question(session.id)
    
    if not next_question:
        # No more questions, session is complete
        chat_service.complete_session(session.id)
        return ChatResponse(
            sessionId=session.id,
            sessionComplete=True
        )
    
    # Convert DB model to schema model
    question_schema = ChatQuestionComplete(
        id=next_question.id,
        sequence=next_question.sequence,
        text=next_question.text,
        description=next_question.description,
        answer_type=next_question.answer_type,
        options=next_question.options,
        required=next_question.required
    )
    
    return ChatResponse(
        sessionId=session.id,
        nextQuestion=question_schema
    )

@router.post("/submit_answer", response_model=ChatResponse)
async def submit_answer(
    answer_data: ChatAnswerData,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit an answer and get the next question
    """
    chat_service = ChatService(db)
    
    # Verify session exists and belongs to the current user or their clinician
    session = chat_service.session_repository.get_by_id(answer_data.sessionId)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check authorization
    if (session.patient_id != current_user.id and  # Not the patient
        current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and  # Not an admin
        (current_user.role != UserRole.CLINICIAN or  # Not a clinician or not the patient's clinician
         session.clinician_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chat session"
        )
    
    # Save the answer
    question = chat_service.question_repository.get_by_id(answer_data.questionId)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    chat_service.save_answer(
        answer_data.sessionId,
        answer_data.questionId,
        answer_data.answer,
        answer_data.answer_value if hasattr(answer_data, "answer_value") else None
    )
    
    # Get the next question
    next_question = chat_service.get_next_question(answer_data.sessionId, answer_data.questionId)
    
    if not next_question:
        # No more questions, session is complete
        chat_service.complete_session(answer_data.sessionId)
        return ChatResponse(
            sessionId=answer_data.sessionId,
            sessionComplete=True
        )
    
    # Convert DB model to schema model
    question_schema = ChatQuestionComplete(
        id=next_question.id,
        sequence=next_question.sequence,
        text=next_question.text,
        description=next_question.description,
        answer_type=next_question.answer_type,
        options=next_question.options,
        required=next_question.required
    )
    
    return ChatResponse(
        sessionId=answer_data.sessionId,
        nextQuestion=question_schema
    )

@router.get("/history/{session_id}", response_model=Dict[str, List[Dict[str, Any]]])
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the chat history for a session
    """
    chat_service = ChatService(db)
    
    # Verify session exists and belongs to the current user or their clinician
    session = chat_service.session_repository.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check authorization
    if (session.patient_id != current_user.id and  # Not the patient
        current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and  # Not an admin
        (current_user.role != UserRole.CLINICIAN or  # Not a clinician or not the patient's clinician
         session.clinician_id != current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chat session"
        )
    
    history = chat_service.get_chat_history(session_id)
    return {"history": history}
