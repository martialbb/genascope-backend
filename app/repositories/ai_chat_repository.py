"""
AI Chat Repository Implementation

This repository handles database operations for AI chat sessions, messages,
and related entities with PostgreSQL-specific optimizations.
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc

from app.repositories.base import BaseRepository
from app.models.ai_chat import (
    AIChatSession, ChatMessage,
    SessionType, SessionStatus, MessageRole, MessageType
)
from app.models.chat_configuration import ChatStrategy, KnowledgeSource


class AIChatRepository(BaseRepository):
    """Repository for AI chat operations with PostgreSQL optimizations."""
    
    def __init__(self, db: Session):
        super().__init__(db, AIChatSession)
    
    # =================== CHAT SESSION OPERATIONS ===================
    
    def create_session(self, session_data: Dict[str, Any]) -> AIChatSession:
        """Create a new AI chat session.
        
        Args:
            session_data: Dictionary containing session attributes
            
        Returns:
            AIChatSession: Created session object
        """
        # Ensure we have a UUID for the session
        if "id" not in session_data:
            session_data["id"] = str(uuid.uuid4())
        
        # Set default values
        session_data.setdefault("status", SessionStatus.active.value)
        session_data.setdefault("started_at", datetime.utcnow())
        session_data.setdefault("last_activity", datetime.utcnow())
        
        session = AIChatSession(**session_data)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session_by_id(self, session_id: str) -> Optional[AIChatSession]:
        """Get a session by ID.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            AIChatSession or None if not found
        """
        return self.db.query(AIChatSession).filter(
            AIChatSession.id == session_id
        ).first()
    
    def get_session_with_messages(self, session_id: str) -> Optional[AIChatSession]:
        """Get session with all related messages and strategy.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            AIChatSession with loaded messages and strategy, or None if not found
        """
        return self.db.query(AIChatSession).options(
            joinedload(AIChatSession.messages),
            joinedload(AIChatSession.strategy)
        ).filter(AIChatSession.id == session_id).first()
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[AIChatSession]:
        """Update a session with new data.
        
        Args:
            session_id: UUID of the session to update
            update_data: Dictionary of attributes to update
            
        Returns:
            Updated AIChatSession or None if not found
        """
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the session
        rows_updated = self.db.query(AIChatSession).filter(
            AIChatSession.id == session_id
        ).update(update_data)
        
        if rows_updated == 0:
            return None
            
        self.db.commit()
        return self.get_session_by_id(session_id)
    
    def get_sessions_by_status(
        self, 
        status: str, 
        patient_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AIChatSession]:
        """Get sessions filtered by status and optional patient ID.
        
        Args:
            status: Session status to filter by
            patient_id: Optional patient ID to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of AIChatSession objects
        """
        query = self.db.query(AIChatSession).filter(
            AIChatSession.status == status
        )
        
        if patient_id:
            query = query.filter(AIChatSession.patient_id == patient_id)
        
        return query.order_by(desc(AIChatSession.last_activity)).limit(limit).all()
    
    def get_sessions_by_patient(self, patient_id: str, limit: int = 50) -> List[AIChatSession]:
        """Get all sessions for a patient, ordered by creation date.
        
        Args:
            patient_id: UUID of the patient
            limit: Maximum number of sessions to return
            
        Returns:
            List of AIChatSession objects
        """
        return self.db.query(AIChatSession).filter(
            AIChatSession.patient_id == patient_id
        ).order_by(desc(AIChatSession.created_at)).limit(limit).all()
    
    def get_active_session_by_patient(self, patient_id: str) -> Optional[AIChatSession]:
        """Get the most recent active session for a patient.
        
        Args:
            patient_id: UUID of the patient
            
        Returns:
            Most recent active AIChatSession or None if not found
        """
        return self.db.query(AIChatSession).filter(
            and_(
                AIChatSession.patient_id == patient_id,
                AIChatSession.status == SessionStatus.active.value
            )
        ).order_by(desc(AIChatSession.last_activity)).first()
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update the last activity timestamp for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            True if session was updated, False if not found
        """
        rows_updated = self.db.query(AIChatSession).filter(
            AIChatSession.id == session_id
        ).update({
            "last_activity": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        self.db.commit()
        return rows_updated > 0
    
    def complete_session(self, session_id: str, assessment_results: Optional[Dict] = None) -> bool:
        """Mark a session as completed with optional assessment results.
        
        Args:
            session_id: UUID of the session
            assessment_results: Optional assessment data to store
            
        Returns:
            True if session was updated, False if not found
        """
        update_data = {
            "status": SessionStatus.completed.value,
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        if assessment_results:
            update_data["assessment_results"] = assessment_results
            
        rows_updated = self.db.query(AIChatSession).filter(
            AIChatSession.id == session_id
        ).update(update_data)
        self.db.commit()
        return rows_updated > 0

    # =================== MESSAGE OPERATIONS ===================
    
    def create_message(self, message_data: Dict[str, Any]) -> ChatMessage:
        """Create a new chat message.
        
        Args:
            message_data: Dictionary containing message attributes
            
        Returns:
            ChatMessage: Created message object
        """
        # Ensure we have a UUID for the message
        if "id" not in message_data:
            message_data["id"] = str(uuid.uuid4())
        
        # Set default timestamp
        message_data.setdefault("created_at", datetime.utcnow())
        
        message = ChatMessage(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get all messages for a session, optionally limited.
        
        Args:
            session_id: UUID of the session
            limit: Optional limit on number of messages to return
            
        Returns:
            List of ChatMessage objects ordered by creation time
        """
        query = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()

    # =================== REFERENCE DATA OPERATIONS ===================
    
    def get_strategy_by_id(self, strategy_id: str) -> Optional[ChatStrategy]:
        """Get a chat strategy by ID.
        
        Args:
            strategy_id: UUID of the chat strategy
            
        Returns:
            ChatStrategy or None if not found
        """
        return self.db.query(ChatStrategy).filter(
            ChatStrategy.id == strategy_id
        ).first()
    
    def get_knowledge_source_by_id(self, source_id: str) -> Optional[KnowledgeSource]:
        """Get a knowledge source by ID.
        
        Args:
            source_id: UUID of the knowledge source
            
        Returns:
            KnowledgeSource or None if not found
        """
        return self.db.query(KnowledgeSource).filter(
            KnowledgeSource.id == source_id
        ).first()
