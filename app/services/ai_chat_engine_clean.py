"""
AI Chat Engine Service

This service orchestrates AI-powered chat conversations by coordinating
between repositories, managing conversation flow, and handling AI responses.
"""
import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.ai_chat_repository import AIChatRepository
from app.models.ai_chat import (
    ChatSession, ChatMessage,
    SessionType, SessionStatus, MessageRole, MessageType
)
from app.models.chat_configuration import ChatStrategy
from app.core.ai_chat_config import get_ai_chat_settings
from app.services.base import BaseService


class ChatEngineService(BaseService):
    """Main service for orchestrating AI chat conversations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db
        self.ai_chat_repo = AIChatRepository(db)
        self.settings = get_ai_chat_settings()
        
        # Initialize related services (lazy import to avoid circular imports)
        self._rag_service = None
        self._extraction_service = None
        self._assessment_service = None
    
    @property
    def rag_service(self):
        if self._rag_service is None:
            from app.services.rag_service import RAGService
            self._rag_service = RAGService(self.db)
        return self._rag_service
    
    @property
    def extraction_service(self):
        if self._extraction_service is None:
            from app.services.entity_extraction import EntityExtractionService
            self._extraction_service = EntityExtractionService(self.db)
        return self._extraction_service
    
    @property
    def assessment_service(self):
        if self._assessment_service is None:
            from app.services.criteria_assessment import CriteriaAssessmentService
            self._assessment_service = CriteriaAssessmentService(self.db)
        return self._assessment_service
    
    async def start_chat_session(
        self, 
        strategy_id: str, 
        patient_id: str, 
        session_type: SessionType,
        initial_context: Optional[dict] = None,
        user_id: Optional[str] = None
    ) -> ChatSession:
        """Start a new AI chat session."""
        
        # Validate strategy exists and get configuration
        strategy = self.ai_chat_repo.get_strategy_by_id(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Chat strategy {strategy_id} not found")
        
        # Create session data
        session_data = {
            "id": str(uuid.uuid4()),
            "strategy_id": strategy_id,
            "patient_id": patient_id,
            "session_type": session_type,
            "status": SessionStatus.active,
            "chat_context": initial_context or {},
            "extracted_data": {},
            "assessment_results": {},
            "started_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "user_id": user_id
        }
        
        # Create session via repository
        session = self.ai_chat_repo.create_session(session_data)
        
        # Create initial welcome message
        welcome_content = self._generate_welcome_message(strategy)
        welcome_message_data = {
            "id": str(uuid.uuid4()),
            "session_id": session.id,
            "role": MessageRole.ASSISTANT,
            "content": welcome_content,
            "message_type": MessageType.TEXT,
            "message_metadata": {"type": "welcome", "strategy_name": strategy.name},
            "created_at": datetime.utcnow()
        }
        
        self.ai_chat_repo.create_message(welcome_message_data)
        
        return session
    
    async def process_user_message(
        self, 
        session_id: str, 
        user_message: str,
        metadata: Optional[dict] = None
    ) -> ChatMessage:
        """Process user message and generate AI response."""
        
        # Get session with messages
        session = self.ai_chat_repo.get_session_with_messages(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Check if session is active
        if session.status != SessionStatus.active:
            raise HTTPException(status_code=400, detail="Session is not active")
        
        # Create user message
        user_msg_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": MessageRole.USER,
            "content": user_message,
            "message_type": MessageType.TEXT,
            "message_metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        
        user_msg = self.ai_chat_repo.create_message(user_msg_data)
        
        # Update session activity
        self.ai_chat_repo.update_session(session_id, {
            "last_activity": datetime.utcnow()
        })
        
        # Extract entities from user message
        extracted_data = await self.extraction_service.extract_entities(user_message, session)
        
        # Update session with extracted data
        if extracted_data:
            updated_extracted_data = {**session.extracted_data, **extracted_data}
            self.ai_chat_repo.update_session(session_id, {
                "extracted_data": updated_extracted_data
            })
            # Update session object for AI response generation
            session.extracted_data = updated_extracted_data
        
        # Get relevant context from knowledge sources
        context = await self.rag_service.get_relevant_context(session_id, user_message)
        
        # Generate AI response
        ai_response = await self._generate_ai_response(session, user_message, context)
        
        # Create assistant message
        assistant_msg_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": MessageRole.ASSISTANT,
            "content": ai_response["content"],
            "message_type": MessageType.TEXT,
            "message_metadata": ai_response.get("metadata", {}),
            "created_at": datetime.utcnow()
        }
        
        assistant_msg = self.ai_chat_repo.create_message(assistant_msg_data)
        
        # Perform assessment if enough data is collected
        await self._try_assessment(session)
        
        # Check if conversation should end
        await self._check_conversation_completion(session)
        
        return assistant_msg
    
    def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get messages for a session."""
        return self.ai_chat_repo.get_session_messages(session_id, limit=limit)
    
    def get_active_sessions(
        self, 
        patient_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[ChatSession]:
        """Get active chat sessions."""
        return self.ai_chat_repo.get_sessions_by_status(
            SessionStatus.active,
            patient_id=patient_id,
            user_id=user_id,
            limit=limit
        )
    
    async def end_session(self, session_id: str, reason: str = "user_ended") -> ChatSession:
        """End a chat session."""
        session = self.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Update session status
        session_data = {
            "status": SessionStatus.completed,
            "ended_at": datetime.utcnow(),
            "session_metadata": {
                **session.session_metadata,
                "end_reason": reason
            }
        }
        
        return self.ai_chat_repo.update_session(session_id, session_data)
    
    async def validate_strategy_access(self, strategy_id: str, user_id: str) -> ChatStrategy:
        """Validate that user has access to the chat strategy."""
        strategy = self.ai_chat_repo.get_strategy_by_id(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Add access control logic here if needed
        return strategy
    
    async def get_session_assessment(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get assessment results for a session."""
        try:
            return await self.assessment_service.assess_session(session_id)
        except Exception as e:
            print(f"Error getting session assessment: {str(e)}")
            return None
    
    async def get_session_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recommendations for a session."""
        try:
            return self.assessment_service.generate_recommendations(session_id)
        except Exception as e:
            print(f"Error getting session recommendations: {str(e)}")
            return []
    
    async def setup_session_context(self, session_id: str) -> None:
        """Setup session context in background (for initial session setup)."""
        try:
            session = self.ai_chat_repo.get_session_by_id(session_id)
            if session:
                # Perform any initial context setup
                strategy = self.ai_chat_repo.get_strategy_by_id(session.strategy_id)
                if strategy and strategy.knowledge_source_ids:
                    # Pre-load any necessary knowledge context
                    pass
        except Exception as e:
            print(f"Error setting up session context: {str(e)}")
    
    def _generate_welcome_message(self, strategy: ChatStrategy) -> str:
        """Generate welcome message based on strategy configuration."""
        if strategy.patient_introduction:
            return strategy.patient_introduction
        
        return f"Hello! I'm here to help with {strategy.name.lower()}. How can I assist you today?"
    
    async def _generate_ai_response(self, session: ChatSession, user_message: str, context: str = "") -> Dict[str, Any]:
        """Generate AI response (placeholder implementation)."""
        # This is a placeholder for AI response generation
        # In a real implementation, this would integrate with OpenAI, LangChain, etc.
        
        strategy = self.ai_chat_repo.get_strategy_by_id(session.strategy_id)
        
        # Enhanced response generation with context
        response_content = self._get_contextual_response(user_message, session, strategy, context)
        
        return {
            "content": response_content,
            "metadata": {
                "response_type": "contextual",
                "strategy_id": strategy.id,
                "message_count": len(session.messages) + 1,
                "has_context": bool(context)
            }
        }
    
    def _get_contextual_response(self, user_message: str, session: ChatSession, strategy: ChatStrategy, context: str) -> str:
        """Generate contextual response using available information."""
        message_lower = user_message.lower()
        message_count = len(session.messages)
        extracted_data = session.extracted_data or {}
        
        # Welcome response
        if message_count <= 1:
            if context:
                return f"Thank you for that information. Based on what I know about {strategy.name.lower()}, let me ask you some questions to better understand your situation."
            return "Thank you for that information. Can you tell me about your medical history?"
        
        # Age-based responses
        if "age" in extracted_data:
            age = extracted_data["age"]
            if message_count == 2:  # First response after age
                if age < 40:
                    return "Thank you for sharing your age. Since you're under 40, family history is particularly important. Can you tell me about any family history of genetic conditions or cancer?"
                else:
                    return "Thank you for your age information. At your age, both personal and family history are important factors. Can you tell me about any family history of genetic conditions?"
        
        # Family history responses
        if "mentioned_family" in extracted_data or "family_history" in extracted_data:
            return "Thank you for sharing about your family history. Have you had any genetic testing done before?"
        
        # Yes/no response handling
        if "last_response" in extracted_data:
            last_response = extracted_data["last_response"]
            if last_response == "yes":
                return "That's helpful information. Can you tell me more details about that?"
            elif last_response == "no":
                return "Thank you for clarifying. Let me ask about something else that might be relevant."
        
        # Context-based responses
        if context:
            if "genetic" in context.lower():
                return "Based on the information available, genetic factors can be important. Are there any specific concerns about genetic risk in your family?"
            elif "testing" in context.lower():
                return "Genetic testing can provide valuable insights. Have you discussed genetic testing with a healthcare provider before?"
        
        # Progressive question flow
        questions_flow = [
            "Can you tell me more about your family medical history?",
            "Have you had any genetic testing done before?",
            "Are there any specific concerns that brought you here today?",
            "Have you experienced any symptoms or health changes recently?",
            "Are you currently working with any healthcare providers for this concern?",
            "Is there anything else you'd like me to know that might be relevant?"
        ]
        
        # Return appropriate question based on message count
        question_index = min((message_count - 2) // 2, len(questions_flow) - 1)
        return questions_flow[question_index]
    
    async def _try_assessment(self, session: ChatSession) -> None:
        """Try to perform assessment if enough data is available."""
        try:
            # Check if we have enough data for assessment
            extracted_data = session.extracted_data or {}
            
            # Simple heuristic: assess if we have at least 3 pieces of information
            if len(extracted_data) >= 3:
                await self.assessment_service.assess_session(session.id)
        except Exception as e:
            # Log error but don't fail the conversation
            print(f"Error in assessment: {str(e)}")
    
    async def _check_conversation_completion(self, session: ChatSession) -> None:
        """Check if conversation should be completed."""
        # Simple completion logic based on message count
        message_count = len(session.messages)
        max_messages = self.settings.max_conversation_turns or 20
        
        if message_count >= max_messages:
            await self.end_session(session.id, "max_messages_reached")
