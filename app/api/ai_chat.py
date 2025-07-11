"""
AI Chat API Endpoints

FastAPI routes for AI-powered chat sessions, message handling,
and knowledge source integration.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.services.ai_chat_engine import ChatEngineService
from app.services.rag_service import RAGService
from app.schemas.ai_chat import (
    StartChatRequest, SendMessageRequest, ChatSessionResponse,
    ChatMessageResponse, SessionAnalyticsResponse
)
from app.models.ai_chat import SessionStatus, SessionType

router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def start_chat_session(
    request: StartChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new AI chat session.
    
    Creates a new AI-powered chat session using the specified strategy
    and sends an initial welcome message to the patient.
    """
    try:
        chat_engine = ChatEngineService(db)
        
        # Validate strategy access
        await chat_engine.validate_strategy_access(request.strategy_id, current_user.id)
        
        # Start session
        session = await chat_engine.start_chat_session(
            strategy_id=request.strategy_id,
            patient_id=request.patient_id,
            session_type=request.session_type,
            initial_context=request.initial_context,
            user_id=current_user.id
        )
        
        # Setup session context in background
        background_tasks.add_task(
            chat_engine.setup_session_context, 
            session.id
        )
        
        # Get message count for response
        messages = chat_engine.get_session_messages(session.id)
        
        # Convert to response model
        session_response = ChatSessionResponse.from_orm(session)
        session_response.message_count = len(messages)
        session_response.progress_percentage = 0.0
        
        return session_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start chat session: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send a message in a chat session and get AI response.
    
    Processes the user's message, extracts relevant information,
    and generates an appropriate AI response based on the conversation context.
    """
    try:
        chat_engine = ChatEngineService(db)
        
        # Validate session exists and user has access
        session = chat_engine.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        # Check session is active
        if session.status != SessionStatus.active.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chat session is not active"
            )
        
        # Process user message and get AI response
        ai_message = await chat_engine.process_user_message(
            session_id=session_id,
            user_message=request.message,
            metadata=request.message_metadata
        )
        
        # Get assessment results in background if available
        background_tasks.add_task(
            chat_engine.get_session_assessment,
            session_id
        )
        
        # Convert to response model
        response = ChatMessageResponse.from_orm(ai_message)
        
        # Add processing metadata
        response.processing_time_ms = 1000  # Placeholder
        response.confidence_score = 0.9  # Placeholder
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get details of a specific chat session."""
    try:
        chat_engine = ChatEngineService(db)
        
        session = chat_engine.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        # Get messages for count and progress calculation
        messages = chat_engine.get_session_messages(session_id)
        
        # Convert to response model
        session_response = ChatSessionResponse.from_orm(session)
        session_response.message_count = len(messages)
        
        # Calculate progress (simple heuristic)
        extracted_count = len(session.extracted_data or {})
        session_response.progress_percentage = min(extracted_count * 20, 100)
        
        return session_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages for a chat session."""
    try:
        chat_engine = ChatEngineService(db)
        
        # Validate session exists
        session = chat_engine.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        messages = chat_engine.get_session_messages(session_id, limit=limit)
        
        # Convert to response models
        message_responses = []
        for message in messages:
            response = ChatMessageResponse.from_orm(message)
            message_responses.append(response)
        
        return message_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session messages: {str(e)}"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    patient_id: Optional[str] = None,
    session_status: Optional[SessionStatus] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get chat sessions for the current user."""
    try:
        chat_engine = ChatEngineService(db)
        
        if session_status == SessionStatus.active.value:
            sessions = chat_engine.get_active_sessions(
                patient_id=patient_id,
                user_id=current_user.id,
                limit=limit
            )
        else:
            # Get all sessions (would need to implement this method)
            sessions = chat_engine.get_active_sessions(
                patient_id=patient_id,
                user_id=current_user.id,
                limit=limit
            )
        
        # Convert to response models
        session_responses = []
        for session in sessions:
            response = ChatSessionResponse.from_orm(session)
            
            # Get message count
            messages = chat_engine.get_session_messages(session.id)
            response.message_count = len(messages)
            
            # Calculate progress
            extracted_count = len(session.extracted_data or {})
            response.progress_percentage = min(extracted_count * 20, 100)
            
            session_responses.append(response)
        
        return session_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.post("/sessions/{session_id}/end", response_model=ChatSessionResponse)
async def end_chat_session(
    session_id: str,
    reason: str = "user_ended",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """End a chat session."""
    try:
        chat_engine = ChatEngineService(db)
        
        session = await chat_engine.end_session(session_id, reason)
        
        # Get final message count
        messages = chat_engine.get_session_messages(session_id)
        
        # Convert to response model
        session_response = ChatSessionResponse.from_orm(session)
        session_response.message_count = len(messages)
        session_response.progress_percentage = 100.0
        
        return session_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end session: {str(e)}"
        )


@router.get("/sessions/{session_id}/assessment")
async def get_session_assessment(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get assessment results for a chat session."""
    try:
        chat_engine = ChatEngineService(db)
        
        # Validate session exists
        session = chat_engine.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        # Get current assessment or perform new assessment
        assessment = await chat_engine.get_session_assessment(session_id)
        
        if not assessment:
            return {"status": "no_assessment", "message": "No assessment available yet"}
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assessment: {str(e)}"
        )


@router.get("/sessions/{session_id}/recommendations")
async def get_session_recommendations(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recommendations based on session assessment."""
    try:
        chat_engine = ChatEngineService(db)
        
        # Validate session exists
        session = chat_engine.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        recommendations = await chat_engine.get_session_recommendations(session_id)
        
        return {
            "session_id": session_id,
            "recommendations": recommendations,
            "generated_at": session.updated_at.isoformat() if session.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )
