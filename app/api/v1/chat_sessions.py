from app.core.ai_chat_config import ai_chat_settings

@router.post("/sessions", response_model=ChatSessionResponse)
async def start_chat_session(
    request: StartChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new AI chat session."""
    
    chat_engine = ChatEngineService(db)
    
    # ...existing validation logic...
    
    session = await chat_engine.start_chat_session(
        strategy_id=request.strategy_id,
        patient_id=request.patient_id,
        session_type=request.session_type,
        initial_context=request.initial_context
    )
    
    # Add mock mode indicator to response
    response = ChatSessionResponse.from_orm(session)
    if ai_chat_settings.should_use_mock_mode:
        response.metadata = response.metadata or {}
        response.metadata["mock_mode"] = True
        response.metadata["mock_mode_warning"] = "Running in development mode without OpenAI integration"
    
    return response

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send a message to the AI chat session."""
    
    chat_engine = ChatEngineService(db)
    
    # ...existing validation logic...
    
    response = await chat_engine.process_patient_response(
        session_id=session_id,
        user_message=request.message,
        metadata=request.message_metadata
    )
    
    # Add mock mode indicator to response
    response_obj = ChatMessageResponse.from_orm(response)
    if ai_chat_settings.should_use_mock_mode and not response_obj.message_metadata:
        response_obj.message_metadata = {}
        response_obj.message_metadata["mock_mode"] = True
    
    return response_obj
