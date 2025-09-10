"""
AI Chat Engine Service

This service orchestrates AI-powered chat conversations by coordinating
between repositories, managing conversation flow, and handling AI responses.
"""
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.ai_chat_repository import AIChatRepository
from app.models.ai_chat import (
    AIChatSession, ChatMessage,
    SessionType, SessionStatus, MessageRole, MessageType
)
from app.models.chat_configuration import ChatStrategy
from app.core.ai_chat_config import get_ai_chat_settings

logger = logging.getLogger(__name__)


class ChatEngineService:
    """Main service for orchestrating AI chat conversations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_chat_repo = AIChatRepository(db)
        self.settings = get_ai_chat_settings()
        
        # Initialize related services (disabled for now - can be re-enabled when implemented)
        # These services will be implemented in future iterations:
        # - RAG Service: For knowledge retrieval and augmented responses
        # - Entity Extraction: For extracting structured data from conversations  
        # - Assessment Service: For evaluating patient criteria and outcomes
        self._rag_service = None
        self._extraction_service = None
        self._assessment_service = None
    
    # =================== CHAT SESSION MANAGEMENT ===================
    
    async def start_chat_session(
        self, 
        strategy_id: str, 
        patient_id: str, 
        session_type: SessionType,
        initial_context: Optional[dict] = None,
        user_id: Optional[str] = None
    ) -> AIChatSession:
        """Start a new AI chat session with initial welcome message.
        
        Args:
            strategy_id: ID of the chat strategy to use
            patient_id: ID of the patient for this session
            session_type: Type of chat session (screening, followup, etc.)
            initial_context: Optional initial context data
            user_id: Optional user ID (for future multi-user support)
            
        Returns:
            AIChatSession: Created session with initial welcome message
            
        Raises:
            HTTPException: If strategy not found
        """
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
            "status": SessionStatus.active.value,
            "chat_context": initial_context or {},
            "extracted_data": {},
            "assessment_results": {},
            "started_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        # Create session via repository
        session = self.ai_chat_repo.create_session(session_data)
        
        # Create initial welcome message
        welcome_content = self._generate_welcome_message(strategy)
        welcome_message_data = {
            "id": str(uuid.uuid4()),
            "session_id": session.id,
            "role": MessageRole.assistant.value,
            "content": welcome_content,
            "message_type": MessageType.response.value,
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
        """Process user message and generate AI response.
        
        Args:
            session_id: ID of the chat session
            user_message: User's message content
            metadata: Optional metadata for the message
            
        Returns:
            ChatMessage: Assistant's response message
            
        Raises:
            HTTPException: If session not found or not active
        """
        # Get session with messages
        session = self.ai_chat_repo.get_session_with_messages(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Check if session is active
        if session.status != SessionStatus.active.value:
            raise HTTPException(status_code=400, detail="Session is not active")
        
        # Create user message
        user_msg_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": MessageRole.user.value,
            "content": user_message,
            "message_type": MessageType.question.value,
            "created_at": datetime.utcnow()
        }
        
        user_msg = self.ai_chat_repo.create_message(user_msg_data)
        
        # Update session activity
        self.ai_chat_repo.update_session(session_id, {
            "last_activity": datetime.utcnow()
        })
        
        # Extract entities from user message (temporarily disabled)
        # This will be implemented when entity extraction service is ready
        extracted_data = {}  
        
        # Update session with extracted data if any
        if extracted_data:
            updated_extracted_data = {**session.extracted_data, **extracted_data}
            self.ai_chat_repo.update_session(session_id, {
                "extracted_data": updated_extracted_data
            })
            session.extracted_data = updated_extracted_data
        
        # Get relevant context from knowledge sources using RAG
        context = await self._get_knowledge_context(session, user_message)
        
        # Generate AI response
        ai_response = await self._generate_ai_response(session, user_message, context)
        
        # Create assistant message
        assistant_msg_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": MessageRole.assistant.value,
            "content": ai_response["content"],
            "message_type": MessageType.response.value,
            "confidence_score": ai_response.get("confidence"),
            "created_at": datetime.utcnow()
        }
        
        assistant_msg = self.ai_chat_repo.create_message(assistant_msg_data)
        
        # Future enhancements (disabled for now):
        # - Perform assessment if enough data is collected
        # - Check if conversation should end based on strategy rules
        
        return assistant_msg
    
    # =================== SESSION RETRIEVAL METHODS ===================
    
    def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get messages for a session.
        
        Args:
            session_id: ID of the chat session
            limit: Optional limit on number of messages
            
        Returns:
            List of ChatMessage objects ordered by creation time
        """
        return self.ai_chat_repo.get_session_messages(session_id, limit=limit)
    
    def get_active_sessions(
        self, 
        patient_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AIChatSession]:
        """Get active chat sessions.
        
        Args:
            patient_id: Optional patient ID to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of active AIChatSession objects
        """
        return self.ai_chat_repo.get_sessions_by_status(
            SessionStatus.active.value,
            patient_id=patient_id,
            limit=limit
        )
    
    async def end_session(self, session_id: str, reason: str = "user_ended") -> Optional[AIChatSession]:
        """End a chat session.
        
        Args:
            session_id: ID of the session to end
            reason: Reason for ending the session
            
        Returns:
            Updated AIChatSession or None if not found
            
        Raises:
            HTTPException: If session not found
        """
        session = self.ai_chat_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Update session status
        session_data = {
            "status": SessionStatus.completed.value,
            "ended_at": datetime.utcnow(),
            "end_reason": reason
        }
        
        return self.ai_chat_repo.update_session(session_id, session_data)
    
    async def validate_strategy_access(self, strategy_id: str, user_id: str) -> ChatStrategy:
        """Validate that user has access to the chat strategy.
        
        Args:
            strategy_id: ID of the chat strategy
            user_id: ID of the user requesting access
            
        Returns:
            ChatStrategy object if access is valid
            
        Raises:
            HTTPException: If strategy not found or access denied
        """
        strategy = self.ai_chat_repo.get_strategy_by_id(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # TODO: Add access control logic here if needed
        # For now, allow access to all strategies
        return strategy
    
    # =================== FUTURE ENHANCEMENTS ===================
    # These methods will be implemented when supporting services are ready
    
    async def get_session_assessment(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get assessment results for a session (placeholder)."""
        # TODO: Implement when assessment service is ready
        return {"status": "not_implemented", "message": "Assessment service not yet implemented"}
    
    async def get_session_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recommendations for a session (placeholder).""" 
        # TODO: Implement when recommendation service is ready
        return [{"type": "placeholder", "message": "Recommendation service not yet implemented"}]
    
    # =================== HELPER METHODS ===================
    
    async def setup_session_context(self, session_id: str) -> None:
        """Setup session context in background (for initial session setup).
        
        Args:
            session_id: ID of the session to setup context for
        """
        try:
            session = self.ai_chat_repo.get_session_by_id(session_id)
            if session:
                strategy = self.ai_chat_repo.get_strategy_by_id(session.strategy_id)
                if strategy and hasattr(strategy, 'knowledge_source_ids') and strategy.knowledge_source_ids:
                    # TODO: Pre-load any necessary knowledge context when RAG service is implemented
                    pass
        except Exception as e:
            print(f"Error setting up session context: {str(e)}")
    
    def _generate_welcome_message(self, strategy: ChatStrategy) -> str:
        """Generate proactive welcome message based on strategy configuration.
        
        This creates an initial proactive message where the AI takes the lead
        in starting the conversation based on the chat strategy.
        
        Args:
            strategy: ChatStrategy object
            
        Returns:
            Proactive welcome message string
        """
        # Generate strategy-specific proactive messages
        strategy_name = strategy.name.lower()
        
        if 'gastroenterology' in strategy_name or 'gastro' in strategy_name:
            return ("Hello! I'm here to help assess your digestive health. I'd like to ask you a few questions "
                   "about any symptoms you might be experiencing. Let's start with: Have you been experiencing "
                   "any abdominal pain, changes in bowel habits, or digestive discomfort recently?")
        elif 'cardiology' in strategy_name or 'heart' in strategy_name:
            return ("Hello! I'm here to help evaluate your cardiovascular health. I'll be asking some questions "
                   "about your heart health and any symptoms you might have. To begin: Have you experienced "
                   "any chest pain, shortness of breath, or heart palpitations lately?")
        elif 'oncology' in strategy_name or 'cancer' in strategy_name:
            return ("Hello! I'm here to help with your health assessment. I'll be asking some important questions "
                   "about your health history and any symptoms. Let's start: Have you noticed any unusual "
                   "changes in your body, such as lumps, persistent fatigue, or unexplained weight loss?")
        elif 'screening' in strategy_name:
            return ("Hello! I'm here to conduct a health screening assessment with you. I'll ask you several "
                   "questions to better understand your current health status. Let's begin: How would you "
                   "describe your overall health right now?")
        else:
            # Generic proactive message
            return (f"Hello! I'm here to help with your {strategy.name.lower()} assessment. I'll be asking "
                   f"you some questions to better understand your health status. Shall we get started with "
                   f"your current symptoms or concerns?")
    
    async def _generate_ai_response(self, session: AIChatSession, user_message: str, context: str = "") -> Dict[str, Any]:
        """Generate AI response using OpenAI API and configured strategy.
        
        Args:
            session: Current chat session
            user_message: User's message content
            context: Additional context from knowledge sources
            
        Returns:
            Dictionary with AI response content and metadata
        """
        import time
        start_time = time.time()
        
        # Get strategy for response configuration
        strategy = self.ai_chat_repo.get_strategy_by_id(session.strategy_id)
        
        try:
            # Use OpenAI API for response generation
            from openai import AsyncOpenAI
            from app.core.ai_chat_config import get_ai_chat_config
            
            config = get_ai_chat_config()
            client = AsyncOpenAI(api_key=config.ai.openai_api_key)
            
            # Build conversation history
            messages = self._build_conversation_history(session, user_message, context, strategy)
            
            # Make OpenAI API call
            response = await client.chat.completions.create(
                model=config.ai.openai_model,
                messages=messages,
                max_tokens=config.ai.openai_max_tokens,
                temperature=config.ai.openai_temperature
            )
            
            response_content = response.choices[0].message.content
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "content": response_content,
                "confidence": 0.95,
                "metadata": {
                    "response_type": "ai_generated",
                    "strategy_id": strategy.id,
                    "strategy_name": strategy.name,
                    "message_count": len(session.messages) + 1,
                    "has_context": bool(context),
                    "response_time_ms": response_time,
                    "model_used": config.ai.openai_model,
                    "tokens_used": response.usage.total_tokens if response.usage else None
                }
            }
            
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}. Using fallback response.")
            # Fallback to rule-based response if OpenAI fails
            response_content = self._get_contextual_response(user_message, session, strategy, context)
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "content": response_content,
                "confidence": 0.7,
                "metadata": {
                    "response_type": "fallback",
                    "strategy_id": strategy.id,
                    "strategy_name": strategy.name,
                    "message_count": len(session.messages) + 1,
                    "has_context": bool(context),
                    "response_time_ms": response_time,
                    "error": str(e)
                }
            }
    
    def _get_contextual_response(self, user_message: str, session: AIChatSession, strategy: ChatStrategy, context: str) -> str:
        """Generate contextual response using available information.
        
        This is a simplified rule-based response system that will be replaced
        with LLM-based generation in the future.
        
        Args:
            user_message: User's message content
            session: Current chat session
            strategy: Chat strategy configuration
            context: Knowledge base context
            
        Returns:
            Generated response string
        """
        message_lower = user_message.lower()
        message_count = len(session.messages)
        extracted_data = session.extracted_data or {}
        
        # Welcome/initial response
        if message_count <= 1:
            if context:
                return f"Thank you for that information. Based on what I know about {strategy.name.lower()}, let me ask you some questions to better understand your situation."
            return "Thank you for that information. Can you tell me about your medical history?"
        
        # Age-based responses (example of data-driven logic)
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
        
        # Context-based responses (when RAG is implemented)
        if context:
            if "genetic" in context.lower():
                return "Based on the information available, genetic factors can be important. Are there any specific concerns about genetic risk in your family?"
            elif "testing" in context.lower():
                return "Genetic testing can provide valuable insights. Have you discussed genetic testing with a healthcare provider before?"
        
        # Progressive question flow (fallback)
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

    def _build_conversation_history(self, session: AIChatSession, user_message: str, context: str, strategy: ChatStrategy) -> List[Dict[str, str]]:
        """Build conversation history for OpenAI API call.
        
        Args:
            session: Current chat session
            user_message: Current user message
            context: Knowledge source context
            strategy: Chat strategy configuration
            
        Returns:
            List of message dictionaries for OpenAI API
        """
        messages = []
        
        # System prompt based on strategy
        system_prompt = self._build_system_prompt(strategy, context)
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history (last 10 messages to stay within token limits)
        recent_messages = session.messages[-10:] if len(session.messages) > 10 else session.messages
        
        for msg in recent_messages:
            if msg.role == "user":
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                messages.append({"role": "assistant", "content": msg.content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _build_system_prompt(self, strategy: ChatStrategy, context: str) -> str:
        """Build system prompt based on strategy and available context.
        
        Args:
            strategy: Chat strategy configuration
            context: Knowledge source context
            
        Returns:
            System prompt string
        """
        base_prompt = f"""You are a helpful medical AI assistant specializing in {strategy.name}. 
You provide accurate, evidence-based medical guidance while emphasizing that patients should consult healthcare providers for diagnosis and treatment.

Your role is to:
- Ask relevant questions to understand the patient's situation
- Provide educational information based on medical guidelines
- Recommend appropriate screening or risk assessment when indicated
- Always emphasize the importance of consulting healthcare professionals

Guidelines:
- Be empathetic and professional
- Ask one question at a time to gather information systematically
- Provide specific, actionable guidance when appropriate
- Reference medical guidelines when relevant
- Always recommend consulting healthcare providers for diagnosis and treatment"""

        if context:
            base_prompt += f"\n\nRelevant medical guidelines and information:\n{context[:1000]}..."
        
        if strategy.description:
            base_prompt += f"\n\nStrategy focus: {strategy.description}"
            
            return base_prompt
    
    async def _get_knowledge_context(self, session: AIChatSession, user_message: str) -> str:
        """Retrieve relevant context from knowledge sources using RAG.
        
        Args:
            session: Current chat session
            user_message: User's message content
            
        Returns:
            Relevant context string from knowledge sources
        """
        try:
            # Get strategy with knowledge sources
            strategy = self.ai_chat_repo.get_strategy_by_id(session.strategy_id)
            
            if not strategy or not strategy.knowledge_sources:
                return ""
            
            # Simple keyword-based retrieval for now
            # In production, this would use vector embeddings and similarity search
            context_parts = []
            
            for knowledge_source in strategy.knowledge_sources:
                if knowledge_source.source_type == "file" and knowledge_source.content:
                    # Simple text search in knowledge source content
                    content = knowledge_source.content.lower()
                    message_lower = user_message.lower()
                    
                    # Check for relevant keywords
                    relevant_keywords = [
                        "brca", "breast cancer", "screening", "mammogram", "mri",
                        "genetic", "hereditary", "family history", "risk assessment",
                        "guidelines", "nccn", "recommendation"
                    ]
                    
                    relevant_score = sum(1 for keyword in relevant_keywords if keyword in message_lower)
                    
                    if relevant_score > 0:
                        # Extract relevant sections (simplified)
                        sentences = knowledge_source.content.split('.')
                        relevant_sentences = []
                        
                        for sentence in sentences[:50]:  # Limit to first 50 sentences
                            sentence_lower = sentence.lower()
                            if any(keyword in sentence_lower for keyword in relevant_keywords):
                                relevant_sentences.append(sentence.strip())
                                if len(relevant_sentences) >= 5:  # Limit context size
                                    break
                        
                        if relevant_sentences:
                            context_parts.append(f"From {knowledge_source.name}:\n" + "\n".join(relevant_sentences))
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.warning(f"Failed to retrieve knowledge context: {e}")
            return ""