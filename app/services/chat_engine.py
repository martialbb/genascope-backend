from app.core.ai_chat_config import ai_chat_settings
from app.services.mock_ai_service import MockAIService

class ChatEngineService:
    """Main service for orchestrating AI chat conversations."""
    
    def __init__(self, db: Session):
        self.db = db
        # ...existing repository initialization...
        
        # Initialize AI services based on configuration
        if ai_chat_settings.should_use_mock_mode:
            self.mock_ai_service = MockAIService()
            self.use_mock_mode = True
        else:
            self.use_mock_mode = False
            # Initialize real AI services
            from app.services.rag_service import RAGService
            from app.services.entity_extraction import EntityExtractionService
            
            self.rag_service = RAGService(db)
            self.extraction_service = EntityExtractionService(db)
    
    async def _generate_ai_response(
        self, 
        session: ChatSession, 
        user_message: str
    ) -> Dict[str, Any]:
        """Generate AI response using appropriate service based on configuration."""
        
        if self.use_mock_mode:
            # Use mock AI service
            conversation_history = self.message_repo.get_session_messages(
                session.id, limit=10
            )
            
            strategy = self._get_strategy_config(session.strategy_id)
            
            return await self.mock_ai_service.generate_response(
                session_id=session.id,
                user_message=user_message,
                conversation_history=[
                    {"role": msg.role, "content": msg.content} 
                    for msg in conversation_history
                ],
                extracted_data=session.extracted_data,
                strategy_config=strategy
            )
        else:
            # Use real AI services
            return await self._generate_real_ai_response(session, user_message)
    
    async def _generate_real_ai_response(
        self, 
        session: ChatSession, 
        user_message: str
    ) -> Dict[str, Any]:
        """Generate AI response using OpenAI and RAG."""
        # ...existing implementation for real AI response...
        pass
    
    def _generate_welcome_message(self, strategy_id: str) -> str:
        """Generate welcome message for new sessions."""
        if self.use_mock_mode:
            strategy = self._get_strategy_config(strategy_id)
            specialty = strategy.get("specialty", "general").lower()
            templates = MOCK_RESPONSE_TEMPLATES.get(specialty, MOCK_RESPONSE_TEMPLATES["general"])
            return templates["welcome"]
        else:
            # Generate real welcome message
            return self._generate_real_welcome_message(strategy_id)
    
    def _get_strategy_config(self, strategy_id: str) -> Dict:
        """Get strategy configuration for AI response generation."""
        # This would normally fetch from database
        # For mock mode, return a basic config
        return {
            "specialty": "oncology",
            "goal": "breast cancer risk assessment",
            "model_config": {}
        }
