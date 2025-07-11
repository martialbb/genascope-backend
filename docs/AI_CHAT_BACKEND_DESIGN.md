# AI-Driven Chat Backend Design

## Overview

This document outlines the comprehensive backend design for the AI-driven patient chat system that enables dynamic, personalized conversations for medical screening and assessment. The system leverages LangChain, RAG (Retrieval-Augmented Generation), and configurable chat strategies to provide intelligent, context-aware patient interactions.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Patient UI    │────│   API Layer     │────│  Service Layer  │
│   (Frontend)    │    │   (FastAPI)     │    │  (Business)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Repository      │────│   AI Engine     │
                       │   Layer         │    │  (LangChain)    │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │────│   pgvector      │
                       │ (PostgreSQL)    │    │ (Embeddings)    │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Chat Sessions   │    │ External Tools  │
                       │   & Messages    │    │ (Risk Calc.)    │
                       └─────────────────┘    └─────────────────┘
```

**Key Architecture Changes:**
- **Unified Database**: All data including vector embeddings stored in PostgreSQL with pgvector extension
- **Simplified RAG**: No separate vector store - embeddings stored directly in database tables
- **Enhanced Performance**: Leverages PostgreSQL's advanced indexing for both similarity and keyword search
                                               └─────────────────┘
```

### Layered Architecture Flow

1. **API Layer** - REST endpoints, request validation, authentication
2. **Service Layer** - Business logic, AI orchestration, workflow management
3. **Repository Layer** - Data access abstraction, query logic
4. **Database Layer** - PostgreSQL storage, relationships, transactions

## Core Components

### 1. Chat Session Management

#### Models

```python
# app/models/chat_session.py
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID, ForeignKey("chat_strategies.id"))
    patient_id = Column(UUID, ForeignKey("patients.id"))
    session_type = Column(Enum(SessionType))  # screening, assessment, follow_up
    status = Column(Enum(SessionStatus))  # active, completed, paused, error
    
    # Context and state
    chat_context = Column(JSON)  # Current conversation state
    extracted_data = Column(JSON)  # Structured information extracted
    assessment_results = Column(JSON)  # AI assessment outcomes
    
    # Configuration snapshot
    strategy_snapshot = Column(JSON)  # Config at session start
    
    # Metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy = relationship("ChatStrategy", back_populates="sessions")
    patient = relationship("Patient", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID, ForeignKey("chat_sessions.id"))
    
    # Message content
    role = Column(Enum(MessageRole))  # user, assistant, system
    content = Column(Text)
    message_type = Column(Enum(MessageType))  # question, response, summary, assessment
    
    # AI processing
    prompt_template = Column(Text)  # Template used for generation
    rag_sources = Column(JSON)  # Knowledge sources referenced
    confidence_score = Column(Float)  # AI confidence in response
    
    # Extracted information
    extracted_entities = Column(JSON)  # NER results
    extracted_intent = Column(String)  # Intent classification
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Integer)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class ExtractionRule(Base):
    __tablename__ = "extraction_rules"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID, ForeignKey("chat_strategies.id"))
    
    # Rule definition
    entity_type = Column(String)  # age, family_history, symptoms
    extraction_method = Column(Enum(ExtractionMethod))  # llm, regex, ner
    pattern = Column(Text)  # Regex pattern or LLM prompt
    validation_rules = Column(JSON)  # Data validation criteria
    
    # Priority and conditions
    priority = Column(Integer, default=1)
    trigger_conditions = Column(JSON)  # When to apply this rule
    
    strategy = relationship("ChatStrategy", back_populates="extraction_rules")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    knowledge_source_id = Column(UUID, ForeignKey("knowledge_sources.id"))
    
    # Content and embedding
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # OpenAI text-embedding-ada-002 dimension
    
    # Chunk metadata
    chunk_index = Column(Integer, nullable=False)
    metadata = Column(JSON)  # Source metadata, page numbers, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    knowledge_source = relationship("KnowledgeSource", back_populates="document_chunks")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_document_chunks_embedding', embedding, postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
        Index('ix_document_chunks_knowledge_source', knowledge_source_id),
        Index('ix_document_chunks_content_fts', func.to_tsvector('english', content), postgresql_using='gin'),
    )
```

#### Enums

```python
# app/schemas/chat_enums.py
class SessionType(str, Enum):
    SCREENING = "screening"
    ASSESSMENT = "assessment"
    FOLLOW_UP = "follow_up"
    CONSULTATION = "consultation"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"
    CANCELLED = "cancelled"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageType(str, Enum):
    QUESTION = "question"
    RESPONSE = "response"
    SUMMARY = "summary"
    ASSESSMENT = "assessment"
    CLARIFICATION = "clarification"

class ExtractionMethod(str, Enum):
    LLM = "llm"
    REGEX = "regex"
    NER = "ner"
    HYBRID = "hybrid"
```

### 2. Repository Layer

```python
# app/repositories/ai_chat.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from app.repositories.base import BaseRepository
from app.models.ai_chat import ChatSession, ChatMessage, ExtractionRule, SessionAnalytics
from app.schemas.ai_chat import SessionType, SessionStatus, MessageRole


class ChatSessionRepository(BaseRepository):
    """Repository for chat session operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, ChatSession)
    
    def create_session(
        self, 
        strategy_id: str, 
        patient_id: str, 
        session_type: SessionType,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            strategy_id=strategy_id,
            patient_id=patient_id,
            session_type=session_type,
            status=SessionStatus.ACTIVE,
            chat_context=initial_context or {},
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.db.add(session)
        self.db.flush()  # Get ID without committing
        return session
    
    def get_session_with_details(self, session_id: str) -> Optional[ChatSession]:
        """Get session with messages and analytics loaded."""
        return (
            self.db.query(ChatSession)
            .options(
                joinedload(ChatSession.messages),
                joinedload(ChatSession.analytics),
                joinedload(ChatSession.strategy)
            )
            .filter(ChatSession.id == session_id)
            .first()
        )
    
    def get_active_sessions_by_patient(self, patient_id: str) -> List[ChatSession]:
        """Get all active sessions for a patient."""
        return (
            self.db.query(ChatSession)
            .filter(
                and_(
                    ChatSession.patient_id == patient_id,
                    ChatSession.status == SessionStatus.ACTIVE
                )
            )
            .order_by(desc(ChatSession.last_activity))
            .all()
        )
    
    def list_sessions_by_account(
        self,
        account_id: str,
        patient_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        session_type: Optional[SessionType] = None,
        status: Optional[SessionStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[ChatSession], int]:
        """List sessions with filtering and pagination."""
        
        # Base query with strategy join to filter by account
        query = (
            self.db.query(ChatSession)
            .join(ChatSession.strategy)
            .filter(ChatSession.strategy.has(account_id=account_id))
        )
        
        # Apply filters
        if patient_id:
            query = query.filter(ChatSession.patient_id == patient_id)
        
        if strategy_id:
            query = query.filter(ChatSession.strategy_id == strategy_id)
        
        if session_type:
            query = query.filter(ChatSession.session_type == session_type)
        
        if status:
            query = query.filter(ChatSession.status == status)
        
        if date_from:
            query = query.filter(ChatSession.started_at >= date_from)
        
        if date_to:
            query = query.filter(ChatSession.started_at <= date_to)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        sessions = (
            query.order_by(desc(ChatSession.started_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return sessions, total_count
    
    def update_session_context(
        self, 
        session_id: str, 
        context_updates: Dict[str, Any]
    ) -> Optional[ChatSession]:
        """Update session context data."""
        session = self.get_by_id(session_id)
        if session:
            # Merge context updates
            current_context = session.chat_context or {}
            current_context.update(context_updates)
            session.chat_context = current_context
            session.last_activity = datetime.utcnow()
            self.db.flush()
        
        return session
    
    def complete_session(
        self, 
        session_id: str, 
        assessment_results: Dict[str, Any]
    ) -> Optional[ChatSession]:
        """Mark session as completed with results."""
        session = self.get_by_id(session_id)
        if session:
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.assessment_results = assessment_results
            self.db.flush()
        
        return session
    
    def get_sessions_requiring_cleanup(self, hours_inactive: int = 24) -> List[ChatSession]:
        """Get sessions that have been inactive for specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_inactive)
        
        return (
            self.db.query(ChatSession)
            .filter(
                and_(
                    ChatSession.status == SessionStatus.ACTIVE,
                    ChatSession.last_activity < cutoff_time
                )
            )
            .all()
        )


class ChatMessageRepository(BaseRepository):
    """Repository for chat message operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, ChatMessage)
    
    def create_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        message_type: str,
        prompt_template: Optional[str] = None,
        rag_sources: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None,
        extracted_entities: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None
    ) -> ChatMessage:
        """Create a new message."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            prompt_template=prompt_template,
            rag_sources=rag_sources,
            confidence_score=confidence_score,
            extracted_entities=extracted_entities,
            processing_time_ms=processing_time_ms,
            created_at=datetime.utcnow()
        )
        
        self.db.add(message)
        self.db.flush()
        return message
    
    def get_session_messages(
        self, 
        session_id: str, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get messages for a session with pagination."""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_latest_message(self, session_id: str) -> Optional[ChatMessage]:
        """Get the most recent message in a session."""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .first()
        )
    
    def get_user_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all user messages in a session."""
        return (
            self.db.query(ChatMessage)
            .filter(
                and_(
                    ChatMessage.session_id == session_id,
                    ChatMessage.role == MessageRole.USER
                )
            )
            .order_by(ChatMessage.created_at)
            .all()
        )
    
    def get_message_count(self, session_id: str) -> int:
        """Get total message count for a session."""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .count()
        )
    
    def get_average_confidence(self, session_id: str) -> Optional[float]:
        """Get average AI confidence score for a session."""
        result = (
            self.db.query(func.avg(ChatMessage.confidence_score))
            .filter(
                and_(
                    ChatMessage.session_id == session_id,
                    ChatMessage.confidence_score.isnot(None)
                )
            )
            .scalar()
        )
        return float(result) if result else None


class ExtractionRuleRepository(BaseRepository):
    """Repository for extraction rule operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, ExtractionRule)
    
    def get_rules_by_strategy(self, strategy_id: str) -> List[ExtractionRule]:
        """Get all extraction rules for a strategy."""
        return (
            self.db.query(ExtractionRule)
            .filter(ExtractionRule.strategy_id == strategy_id)
            .order_by(ExtractionRule.priority.asc())
            .all()
        )
    
    def get_rules_by_entity_type(
        self, 
        strategy_id: str, 
        entity_type: str
    ) -> List[ExtractionRule]:
        """Get extraction rules for a specific entity type."""
        return (
            self.db.query(ExtractionRule)
            .filter(
                and_(
                    ExtractionRule.strategy_id == strategy_id,
                    ExtractionRule.entity_type == entity_type
                )
            )
            .order_by(ExtractionRule.priority.asc())
            .all()
        )


class SessionAnalyticsRepository(BaseRepository):
    """Repository for session analytics operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, SessionAnalytics)
    
    def create_or_update_analytics(
        self,
        session_id: str,
        **analytics_data
    ) -> SessionAnalytics:
        """Create or update analytics for a session."""
        analytics = (
            self.db.query(SessionAnalytics)
            .filter(SessionAnalytics.session_id == session_id)
            .first()
        )
        
        if analytics:
            # Update existing
            for key, value in analytics_data.items():
                if hasattr(analytics, key):
                    setattr(analytics, key, value)
            analytics.updated_at = datetime.utcnow()
        else:
            # Create new
            analytics = SessionAnalytics(
                session_id=session_id,
                **analytics_data
            )
            self.db.add(analytics)
        
        self.db.flush()
        return analytics
    
    def get_analytics_by_strategy(
        self, 
        strategy_id: str, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[SessionAnalytics]:
        """Get analytics for all sessions of a strategy."""
        query = (
            self.db.query(SessionAnalytics)
            .join(SessionAnalytics.session)
            .filter(SessionAnalytics.session.has(strategy_id=strategy_id))
        )
        
        if date_from:
            query = query.filter(SessionAnalytics.created_at >= date_from)
        
        if date_to:
            query = query.filter(SessionAnalytics.created_at <= date_to)
        
        return query.all()
    
    def get_completion_rate_stats(self, strategy_id: str) -> Dict[str, Any]:
        """Get completion rate statistics for a strategy."""
        result = (
            self.db.query(
                func.avg(SessionAnalytics.completion_rate).label('avg_completion'),
                func.min(SessionAnalytics.completion_rate).label('min_completion'),
                func.max(SessionAnalytics.completion_rate).label('max_completion'),
                func.count(SessionAnalytics.id).label('total_sessions')
            )
            .join(SessionAnalytics.session)
            .filter(SessionAnalytics.session.has(strategy_id=strategy_id))
            .first()
        )
        
        return {
            'average_completion_rate': float(result.avg_completion) if result.avg_completion else 0.0,
            'min_completion_rate': float(result.min_completion) if result.min_completion else 0.0,
            'max_completion_rate': float(result.max_completion) if result.max_completion else 0.0,
            'total_sessions': result.total_sessions or 0
        }
}


class DocumentChunkRepository(BaseRepository):
    """Repository for document chunk operations with pgvector."""
    
    def __init__(self, db: Session):
        super().__init__(db, DocumentChunk)
    
    def create_document_chunk(self, chunk_data: Dict[str, Any]) -> DocumentChunk:
        """Create a new document chunk with embedding."""
        chunk = DocumentChunk(
            knowledge_source_id=chunk_data["knowledge_source_id"],
            content=chunk_data["content"],
            embedding=chunk_data["embedding"],
            chunk_index=chunk_data["chunk_index"],
            metadata=chunk_data["metadata"]
        )
        
        self.db.add(chunk)
        self.db.flush()
        return chunk
    
    def similarity_search(
        self,
        query_embedding: List[float],
        source_ids: List[str],
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform similarity search using pgvector."""
        
        # Convert query embedding to pgvector format
        query_vector = f"[{','.join(map(str, query_embedding))}]"
        
        # Perform cosine similarity search
        results = (
            self.db.query(
                DocumentChunk,
                (DocumentChunk.embedding.cosine_distance(query_vector)).label('similarity_score')
            )
            .filter(DocumentChunk.knowledge_source_id.in_(source_ids))
            .filter(DocumentChunk.embedding.cosine_distance(query_vector) < (1 - similarity_threshold))
            .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            .limit(limit)
            .all()
        )
        
        # Format results
        formatted_results = []
        for chunk, similarity_score in results:
            chunk_dict = {
                "id": chunk.id,
                "knowledge_source_id": chunk.knowledge_source_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata,
                "similarity_score": 1 - similarity_score,  # Convert distance to similarity
                "created_at": chunk.created_at
            }
            formatted_results.append(chunk_dict)
        
        return formatted_results
    
    def keyword_search(
        self,
        keywords: List[str],
        source_ids: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform full-text search using PostgreSQL."""
        
        # Create tsquery from keywords
        search_query = " & ".join(keywords)
        
        results = (
            self.db.query(
                DocumentChunk,
                func.ts_rank(func.to_tsvector('english', DocumentChunk.content), 
                           func.to_tsquery('english', search_query)).label('rank_score')
            )
            .filter(DocumentChunk.knowledge_source_id.in_(source_ids))
            .filter(func.to_tsvector('english', DocumentChunk.content).match(search_query))
            .order_by(desc(func.ts_rank(func.to_tsvector('english', DocumentChunk.content), 
                                      func.to_tsquery('english', search_query))))
            .limit(limit)
            .all()
        )
        
        # Format results
        formatted_results = []
        for chunk, rank_score in results:
            chunk_dict = {
                "id": chunk.id,
                "knowledge_source_id": chunk.knowledge_source_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata,
                "rank_score": float(rank_score),
                "created_at": chunk.created_at
            }
            formatted_results.append(chunk_dict)
        
        return formatted_results
    
    def get_chunks_by_source(self, source_id: str) -> List[DocumentChunk]:
        """Get all chunks for a knowledge source."""
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.knowledge_source_id == source_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )
    
    def delete_chunks_by_source(self, source_id: str) -> int:
        """Delete all chunks for a knowledge source."""
        deleted_count = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.knowledge_source_id == source_id)
            .delete()
        )
        self.db.flush()
        return deleted_count
    
    def get_chunk_count_by_source(self, source_id: str) -> int:
        """Get total chunk count for a knowledge source."""
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.knowledge_source_id == source_id)
            .count()
        )
```

### 3. Service Layer

```python
# app/services/ai_chat_service.py
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.ai_chat import (
    ChatSessionRepository, 
    ChatMessageRepository, 
    ExtractionRuleRepository,
    SessionAnalyticsRepository,
    DocumentChunkRepository
)
from app.services.chat_engine import ChatEngineService
from app.services.entity_extraction import EntityExtractionService
from app.services.criteria_assessment import CriteriaAssessmentService
from app.schemas.ai_chat import (
    StartChatRequest, SendMessageRequest, ChatSessionResponse,
    ChatMessageResponse, SessionType, SessionStatus, MessageRole
)
from app.models.ai_chat import ChatSession, ChatMessage


class AIChatService:
    """Service layer for AI chat operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = ChatMessageRepository(db)
        self.extraction_repo = ExtractionRuleRepository(db)
        self.analytics_repo = SessionAnalyticsRepository(db)
        self.chunk_repo = DocumentChunkRepository(db)
        
        # AI services
        self.chat_engine = ChatEngineService(db)
        self.extraction_service = EntityExtractionService(db)
        self.assessment_service = CriteriaAssessmentService(db)
    
    def start_chat_session(
        self,
        request: StartChatRequest,
        user_id: str,
        account_id: str
    ) -> ChatSessionResponse:
        """Start a new AI chat session."""
        
        # Validate strategy access
        strategy = self._validate_strategy_access(request.strategy_id, account_id)
        
        # Check session limits
        self._check_session_limits(request.patient_id)
        
        # Create session
        session = self.session_repo.create_session(
            strategy_id=request.strategy_id,
            patient_id=request.patient_id,
            session_type=request.session_type,
            initial_context=request.initial_context
        )
        
        # Set strategy snapshot
        session.strategy_snapshot = self._create_strategy_snapshot(strategy)
        
        # Generate initial AI message
        initial_message = self.chat_engine.generate_initial_question(
            session, strategy
        )
        
        # Store initial message
        self.message_repo.create_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=initial_message.content,
            message_type="question",
            prompt_template=initial_message.prompt_used,
            confidence_score=initial_message.confidence
        )
        
        # Initialize analytics
        self.analytics_repo.create_or_update_analytics(
            session_id=session.id,
            total_messages=1
        )
        
        self.db.commit()
        
        return self._to_session_response(session)
    
    def send_message(
        self,
        session_id: str,
        request: SendMessageRequest,
        user_id: str
    ) -> ChatMessageResponse:
        """Process a patient message and generate AI response."""
        
        # Validate session access
        session = self._validate_session_access(session_id, user_id)
        
        # Check session is active
        if session.status != SessionStatus.ACTIVE:
            raise ValueError("Session is not active")
        
        # Store user message
        user_message = self.message_repo.create_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=request.message,
            message_type="response"
        )
        
        # Extract entities from user message
        extracted_data = self.extraction_service.extract_entities(
            request.message,
            session.strategy_snapshot
        )
        
        # Update user message with extracted entities
        user_message.extracted_entities = extracted_data
        
        # Update session context
        context_updates = {
            "collected_data": {**session.chat_context.get("collected_data", {}), **extracted_data},
            "last_user_message": request.message
        }
        self.session_repo.update_session_context(session_id, context_updates)
        
        # Check if assessment can be performed
        can_assess = self.assessment_service.can_assess(session)
        
        if can_assess:
            # Generate final assessment
            ai_response = self.chat_engine.generate_assessment(session)
            message_type = "assessment"
            
            # Complete session with assessment results
            self.session_repo.complete_session(
                session_id, 
                ai_response.assessment_data
            )
        else:
            # Generate next question
            ai_response = self.chat_engine.generate_next_question(session)
            message_type = "question"
        
        # Store AI response
        ai_message = self.message_repo.create_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            message_type=message_type,
            prompt_template=ai_response.prompt_used,
            rag_sources=ai_response.rag_sources,
            confidence_score=ai_response.confidence,
            processing_time_ms=ai_response.processing_time_ms
        )
        
        # Update analytics
        self._update_session_analytics(session_id)
        
        self.db.commit()
        
        return self._to_message_response(ai_message)
    
    def get_chat_session(
        self,
        session_id: str,
        user_id: str
    ) -> ChatSessionResponse:
        """Get chat session details."""
        session = self._validate_session_access(session_id, user_id)
        return self._to_session_response(session)
    
    def get_chat_messages(
        self,
        session_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatMessageResponse]:
        """Get messages for a chat session."""
        # Validate access
        self._validate_session_access(session_id, user_id)
        
        # Get messages
        messages = self.message_repo.get_session_messages(session_id, skip, limit)
        
        return [self._to_message_response(msg) for msg in messages]
    
    def list_chat_sessions(
        self,
        account_id: str,
        patient_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        session_type: Optional[SessionType] = None,
        status: Optional[SessionStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[ChatSessionResponse], int]:
        """List chat sessions with filtering."""
        
        sessions, total_count = self.session_repo.list_sessions_by_account(
            account_id=account_id,
            patient_id=patient_id,
            strategy_id=strategy_id,
            session_type=session_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        
        session_responses = [self._to_session_response(s) for s in sessions]
        
        return session_responses, total_count
    
    def _validate_strategy_access(self, strategy_id: str, account_id: str):
        """Validate user has access to strategy."""
        # Implementation would check strategy belongs to account
        # For now, assume validation passes
        return {"id": strategy_id, "account_id": account_id}
    
    def _validate_session_access(self, session_id: str, user_id: str) -> ChatSession:
        """Validate user has access to session."""
        session = self.session_repo.get_session_with_details(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Additional access validation would go here
        return session
    
    def _check_session_limits(self, patient_id: str):
        """Check if patient has too many active sessions."""
        active_sessions = self.session_repo.get_active_sessions_by_patient(patient_id)
        if len(active_sessions) >= 3:  # Configurable limit
            raise ValueError("Too many active sessions for this patient")
    
    def _create_strategy_snapshot(self, strategy) -> Dict[str, Any]:
        """Create a snapshot of strategy configuration."""
        return {
            "id": strategy["id"],
            "goal": strategy.get("goal", ""),
            "extraction_rules": [],  # Would be populated from strategy
            "assessment_criteria": {}  # Would be populated from strategy
        }
    
    def _update_session_analytics(self, session_id: str):
        """Update analytics for a session."""
        message_count = self.message_repo.get_message_count(session_id)
        avg_confidence = self.message_repo.get_average_confidence(session_id)
        
        self.analytics_repo.create_or_update_analytics(
            session_id=session_id,
            total_messages=message_count,
            ai_confidence_avg=avg_confidence
        )
    
    def _to_session_response(self, session: ChatSession) -> ChatSessionResponse:
        """Convert session model to response."""
        message_count = self.message_repo.get_message_count(session.id)
        
        return ChatSessionResponse(
            id=str(session.id),
            strategy_id=str(session.strategy_id),
            patient_id=str(session.patient_id),
            session_type=session.session_type,
            status=session.status,
            chat_context=session.chat_context,
            extracted_data=session.extracted_data,
            assessment_results=session.assessment_results,
            started_at=session.started_at,
            completed_at=session.completed_at,
            last_activity=session.last_activity,
            message_count=message_count,
            progress_percentage=self._calculate_progress(session)
        )
    
    def _to_message_response(self, message: ChatMessage) -> ChatMessageResponse:
        """Convert message model to response."""
        return ChatMessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            role=message.role,
            content=message.content,
            message_type=message.message_type,
            created_at=message.created_at,
            confidence_score=message.confidence_score,
            rag_sources=message.rag_sources,
            processing_time_ms=message.processing_time_ms,
            extracted_entities=message.extracted_entities,
            extracted_intent=message.extracted_intent
        )
    
    def _calculate_progress(self, session: ChatSession) -> float:
        """Calculate session completion progress."""
        # Implementation would calculate based on required information collected
        return 50.0  # Placeholder
```

### 4. Updated Chat Engine Service

```python
# app/services/chat_engine.py
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

class ChatEngineService:
    """Core AI chat engine using LangChain."""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = self._initialize_llm()
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = self._initialize_vector_store()
        self.extraction_service = EntityExtractionService(db)
        self.assessment_service = CriteriaAssessmentService(db)
        
    def start_chat_session(
        self, 
        strategy_id: str, 
        patient_id: str,
        session_type: SessionType = SessionType.SCREENING
    ) -> ChatSession:
        """Initialize a new chat session."""
        # Load strategy configuration
        strategy = self._load_strategy(strategy_id)
        
        # Create session
        session = ChatSession(
            strategy_id=strategy_id,
            patient_id=patient_id,
            session_type=session_type,
            status=SessionStatus.ACTIVE,
            strategy_snapshot=strategy.to_dict(),
            chat_context={
                "goal": strategy.goal,
                "collected_data": {},
                "next_questions": [],
                "assessment_progress": 0
            }
        )
        
        self.db.add(session)
        self.db.commit()
        
        # Generate initial question
        initial_message = self._generate_initial_question(session, strategy)
        
        return session
    
    def process_patient_response(
        self, 
        session_id: str, 
        user_message: str
    ) -> ChatMessage:
        """Process patient response and generate next question."""
        session = self._load_session(session_id)
        
        # 1. Store user message
        user_msg = self._store_message(
            session_id, 
            MessageRole.USER, 
            user_message,
            MessageType.RESPONSE
        )
        
        # 2. Extract information from response
        extracted_data = self.extraction_service.extract_entities(
            user_message, 
            session.strategy_snapshot
        )
        
        # 3. Update session context
        self._update_session_context(session, extracted_data)
        
        # 4. Check if assessment can be performed
        assessment_ready = self.assessment_service.can_assess(session)
        
        if assessment_ready:
            # Generate final assessment
            response = self._generate_assessment(session)
            session.status = SessionStatus.COMPLETED
        else:
            # Generate next question
            response = self._generate_next_question(session)
        
        # 5. Store AI response
        ai_message = self._store_message(
            session_id,
            MessageRole.ASSISTANT,
            response.content,
            MessageType.ASSESSMENT if assessment_ready else MessageType.QUESTION,
            prompt_template=response.prompt_used,
            rag_sources=response.rag_sources,
            confidence_score=response.confidence
        )
        
        self.db.commit()
        return ai_message
    
    def _generate_initial_question(
        self, 
        session: ChatSession, 
        strategy: ChatStrategy
    ) -> ChatMessage:
        """Generate the opening question using LangChain."""
        
        # Build context from strategy and knowledge sources
        context = self._build_rag_context(strategy, query="initial question")
        
        prompt = PromptTemplate(
            input_variables=["goal", "context", "patient_introduction"],
            template="""
            You are an empathetic AI assistant helping with medical screening.
            
            GOAL: {goal}
            
            CONTEXT: {context}
            
            PATIENT INTRODUCTION: {patient_introduction}
            
            Generate a warm, empathetic opening question that begins the conversation
            toward achieving the stated goal. Be conversational and reassuring.
            
            QUESTION:
            """
        )
        
        response = self.llm(
            prompt.format(
                goal=strategy.goal,
                context=context,
                patient_introduction=strategy.patient_introduction
            )
        )
        
        return self._store_message(
            session.id,
            MessageRole.ASSISTANT,
            response,
            MessageType.QUESTION,
            prompt_template=prompt.template
        )
    
    def _generate_next_question(self, session: ChatSession) -> AIResponse:
        """Generate next question based on current context."""
        context = session.chat_context
        collected_data = context.get("collected_data", {})
        goal = context.get("goal")
        
        # Determine what information is still needed
        missing_info = self._analyze_missing_information(session)
        
        # Build RAG context for next question
        rag_context = self._build_rag_context(
            session.strategy, 
            query=f"next question about {missing_info}"
        )
        
        prompt = PromptTemplate(
            input_variables=["goal", "collected_data", "missing_info", "context"],
            template="""
            You are conducting a medical screening conversation.
            
            GOAL: {goal}
            COLLECTED DATA: {collected_data}
            STILL NEEDED: {missing_info}
            KNOWLEDGE CONTEXT: {context}
            
            Based on what we've learned so far, generate the next most important 
            question to gather the missing information. Be empathetic and clear.
            
            NEXT QUESTION:
            """
        )
        
        response = self.llm(
            prompt.format(
                goal=goal,
                collected_data=collected_data,
                missing_info=missing_info,
                context=rag_context
            )
        )
        
        return AIResponse(
            content=response,
            prompt_used=prompt.template,
            rag_sources=rag_context.get("sources", []),
            confidence=0.85  # Could be computed
        )
    
    def _generate_assessment(self, session: ChatSession) -> AIResponse:
        """Generate final assessment and recommendations."""
        collected_data = session.chat_context.get("collected_data", {})
        
        # Use assessment service to check criteria
        assessment_results = self.assessment_service.assess_criteria(
            session, 
            collected_data
        )
        
        # Generate explanation using LLM
        prompt = PromptTemplate(
            input_variables=["collected_data", "assessment_results"],
            template="""
            Based on the patient's responses, provide a clear, empathetic summary
            and next steps.
            
            PATIENT DATA: {collected_data}
            ASSESSMENT: {assessment_results}
            
            Provide:
            1. A summary of what was discussed
            2. The assessment outcome in patient-friendly language
            3. Clear next steps
            
            Be reassuring and professional.
            
            SUMMARY:
            """
        )
        
        response = self.llm(
            prompt.format(
                collected_data=collected_data,
                assessment_results=assessment_results
            )
        )
        
        # Store assessment results
        session.assessment_results = assessment_results
        session.completed_at = datetime.utcnow()
        
        return AIResponse(
            content=response,
            prompt_used=prompt.template,
            assessment_data=assessment_results,
            confidence=0.9
        )
```

### 3. Entity Extraction Service

```python
# app/services/entity_extraction.py
import spacy
import re
from typing import Dict, List, Any
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

class EntityExtractionService:
    """Service for extracting structured information from patient responses."""
    
    def __init__(self, db: Session):
        self.db = db
        self.nlp = spacy.load("en_core_web_sm")
        self.llm = OpenAI(temperature=0.1)  # Low temperature for extraction
        
    def extract_entities(
        self, 
        message: str, 
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract entities using multiple methods."""
        
        extracted = {}
        
        # 1. Named Entity Recognition (spaCy)
        ner_entities = self._extract_with_ner(message)
        extracted.update(ner_entities)
        
        # 2. Regex patterns (for specific medical terms)
        regex_entities = self._extract_with_regex(message, strategy_config)
        extracted.update(regex_entities)
        
        # 3. LLM-based extraction (for complex reasoning)
        llm_entities = self._extract_with_llm(message, strategy_config)
        extracted.update(llm_entities)
        
        # 4. Validate and clean extracted data
        validated = self._validate_extracted_data(extracted, strategy_config)
        
        return validated
    
    def _extract_with_ner(self, message: str) -> Dict[str, Any]:
        """Extract entities using spaCy NER."""
        doc = self.nlp(message)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ == "DATE":
                entities["dates"] = entities.get("dates", []) + [ent.text]
            elif ent.label_ == "PERSON":
                entities["people"] = entities.get("people", []) + [ent.text]
            elif ent.label_ in ["CARDINAL", "QUANTITY"]:
                entities["numbers"] = entities.get("numbers", []) + [ent.text]
        
        return entities
    
    def _extract_with_regex(
        self, 
        message: str, 
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract using predefined regex patterns."""
        patterns = {
            "age": r'\b(\d{1,3})\s*(?:years?\s*old|yo|y\.o\.)\b',
            "cancer_types": r'\b(breast|lung|colon|prostate|ovarian)\s*cancer\b',
            "family_relations": r'\b(mother|father|sister|brother|grandmother|grandfather)\b',
            "yes_no": r'\b(yes|no|yeah|nope|yep)\b'
        }
        
        extracted = {}
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, message.lower())
            if matches:
                extracted[entity_type] = matches
        
        return extracted
    
    def _extract_with_llm(
        self, 
        message: str, 
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract complex information using LLM reasoning."""
        
        prompt = PromptTemplate(
            input_variables=["message", "extraction_targets"],
            template="""
            Extract the following information from the patient's message.
            Return ONLY a JSON object with the extracted data.
            
            MESSAGE: "{message}"
            
            EXTRACT:
            - family_history: List of family members with cancer and their cancer types
            - symptoms: Any symptoms mentioned
            - medical_history: Personal medical history items
            - concerns: Patient concerns or worries
            - timeline: Any dates or time references
            
            JSON:
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(
            message=message,
            extraction_targets="family_history, symptoms, medical_history, concerns"
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}
    
    def _validate_extracted_data(
        self, 
        extracted: Dict[str, Any], 
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and normalize extracted data."""
        validated = {}
        
        # Age validation
        if "age" in extracted:
            ages = extracted["age"]
            for age in ages:
                try:
                    age_num = int(age)
                    if 0 <= age_num <= 150:
                        validated["age"] = age_num
                        break
                except ValueError:
                    continue
        
        # Cancer type normalization
        if "cancer_types" in extracted:
            cancer_map = {
                "breast": "breast_cancer",
                "lung": "lung_cancer",
                "colon": "colorectal_cancer"
            }
            validated["cancer_types"] = [
                cancer_map.get(cancer, cancer) 
                for cancer in extracted["cancer_types"]
            ]
        
        return validated
```

### 4. Criteria Assessment Service

```python
# app/services/criteria_assessment.py
from typing import Dict, List, Any, Optional
from langchain.agents import initialize_agent, Tool
from langchain.tools import BaseTool

class CriteriaAssessmentService:
    """Service for assessing if collected data meets defined criteria."""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = OpenAI(temperature=0)
        self.tools = self._initialize_tools()
        
    def can_assess(self, session: ChatSession) -> bool:
        """Determine if enough information has been collected for assessment."""
        strategy = session.strategy_snapshot
        collected_data = session.chat_context.get("collected_data", {})
        
        required_fields = strategy.get("required_information", [])
        
        # Check if all required fields have been collected
        for field in required_fields:
            if field not in collected_data or not collected_data[field]:
                return False
        
        return True
    
    def assess_criteria(
        self, 
        session: ChatSession, 
        collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess collected data against strategy criteria."""
        
        strategy = session.strategy_snapshot
        criteria = strategy.get("assessment_criteria", {})
        
        results = {
            "meets_criteria": False,
            "criteria_checked": [],
            "recommendations": [],
            "risk_scores": {},
            "next_steps": []
        }
        
        # 1. Rule-based assessment
        rule_results = self._assess_rules(collected_data, criteria)
        results.update(rule_results)
        
        # 2. LLM-based reasoning assessment
        llm_assessment = self._assess_with_llm(collected_data, criteria)
        results["llm_reasoning"] = llm_assessment
        
        # 3. External tool integration (e.g., risk calculators)
        if "risk_calculation" in criteria:
            risk_scores = self._calculate_risk_scores(collected_data, criteria)
            results["risk_scores"] = risk_scores
        
        # 4. Generate recommendations
        recommendations = self._generate_recommendations(results, criteria)
        results["recommendations"] = recommendations
        
        return results
    
    def _assess_rules(
        self, 
        data: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess using rule-based logic."""
        
        results = {
            "rule_based_assessment": True,
            "criteria_met": []
        }
        
        # Example: Breast cancer genetic testing criteria
        if criteria.get("type") == "brca_screening":
            meets_age = data.get("age", 0) >= criteria.get("min_age", 25)
            has_family_history = bool(data.get("family_history"))
            
            if meets_age and has_family_history:
                results["criteria_met"].append("age_and_family_history")
                results["meets_criteria"] = True
        
        return results
    
    def _assess_with_llm(
        self, 
        data: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM for complex criteria assessment."""
        
        prompt = PromptTemplate(
            input_variables=["data", "criteria"],
            template="""
            You are a medical screening AI. Assess if the patient data meets
            the specified criteria.
            
            PATIENT DATA: {data}
            CRITERIA: {criteria}
            
            Provide your assessment in JSON format:
            {{
                "meets_criteria": true/false,
                "reasoning": "explanation",
                "confidence": 0.0-1.0,
                "recommendations": ["rec1", "rec2"]
            }}
            
            ASSESSMENT:
            """
        )
        
        response = self.llm(
            prompt.format(data=data, criteria=criteria)
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM assessment"}
    
    def _calculate_risk_scores(
        self, 
        data: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate risk scores using external tools."""
        
        scores = {}
        
        # Tyrer-Cuzick score calculation
        if "tyrer_cuzick" in criteria.get("risk_models", []):
            tc_score = self._calculate_tyrer_cuzick(data)
            scores["tyrer_cuzick"] = tc_score
        
        # Gail model
        if "gail_model" in criteria.get("risk_models", []):
            gail_score = self._calculate_gail_model(data)
            scores["gail_model"] = gail_score
        
        return scores
    
    def _calculate_tyrer_cuzick(self, data: Dict[str, Any]) -> float:
        """Calculate Tyrer-Cuzick risk score."""
        # This would integrate with an external risk calculator
        # For now, return a mock calculation
        age = data.get("age", 50)
        has_family_history = bool(data.get("family_history"))
        
        base_risk = 0.12  # 12% lifetime risk baseline
        if has_family_history:
            base_risk *= 2.0
        
        if age > 50:
            base_risk *= 1.2
        
        return min(base_risk, 0.8)  # Cap at 80%
    
    def _generate_recommendations(
        self, 
        assessment_results: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized recommendations."""
        
        recommendations = []
        
        if assessment_results.get("meets_criteria"):
            recommendations.extend([
                "Discuss genetic counseling with your clinician",
                "Consider genetic testing for BRCA1/BRCA2 mutations",
                "Review family history with a genetic counselor"
            ])
        else:
            recommendations.extend([
                "Continue routine screening as recommended by your clinician",
                "Maintain a healthy lifestyle",
                "Report any new symptoms to your healthcare provider"
            ])
        
        return recommendations

class TyrerCuzickTool(BaseTool):
    """Tool for calculating Tyrer-Cuzick risk scores."""
    
    name = "tyrer_cuzick_calculator"
    description = "Calculate breast cancer risk using Tyrer-Cuzick model"
    
    def _run(self, patient_data: str) -> str:
        """Run the Tyrer-Cuzick calculation."""
        # This would integrate with actual risk calculator service
        return "Risk calculation: 15.2% lifetime risk"
    
    async def _arun(self, patient_data: str) -> str:
        """Async version of the calculation."""
        return self._run(patient_data)
```

### 5. RAG Integration Service

```python
# app/services/rag_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from app.repositories.knowledge_source_repository import KnowledgeSourceRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository

class RAGService:
    """Service for Retrieval-Augmented Generation using pgvector."""
    
    def __init__(self, db: Session):
        self.db = db
        self.embeddings = OpenAIEmbeddings()
        self.knowledge_repo = KnowledgeSourceRepository(db)
        self.chunk_repo = DocumentChunkRepository(db)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    async def index_knowledge_source(self, knowledge_source: KnowledgeSource):
        """Index a knowledge source for RAG retrieval using pgvector."""
        
        try:
            # Load document content
            documents = self._load_document_content(knowledge_source)
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.embeddings.aembed_query(chunk.page_content)
                
                # Create document chunk with metadata
                chunk_data = {
                    "knowledge_source_id": knowledge_source.id,
                    "content": chunk.page_content,
                    "embedding": embedding,
                    "chunk_index": i,
                    "metadata": {
                        "source_id": knowledge_source.id,
                        "source_type": knowledge_source.source_type,
                        "specialty": knowledge_source.specialty,
                        "title": knowledge_source.title,
                        **chunk.metadata
                    }
                }
                
                # Store in database via repository
                self.chunk_repo.create_document_chunk(chunk_data)
            
            # Update knowledge source status via repository
            self.knowledge_repo.update_processing_status(
                knowledge_source.id, 
                ProcessingStatus.COMPLETED
            )
            
        except Exception as e:
            # Update failed status via repository
            self.knowledge_repo.update_processing_status(
                knowledge_source.id, 
                ProcessingStatus.FAILED,
                error_message=str(e)
            )
            raise
    
    async def retrieve_relevant_content(
        self, 
        query: str, 
        strategy_id: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant content for a query using pgvector similarity search."""
        
        # Generate query embedding
        query_embedding = await self.embeddings.aembed_query(query)
        
        # Get relevant knowledge sources for the strategy
        source_ids = self.knowledge_repo.get_source_ids_by_strategy(strategy_id)
        
        # Perform similarity search using pgvector
        similar_chunks = self.chunk_repo.similarity_search(
            query_embedding=query_embedding,
            source_ids=source_ids,
            limit=k
        )
        
        # Format results
        formatted_results = []
        for chunk in similar_chunks:
            formatted_results.append({
                "content": chunk.content,
                "metadata": chunk.metadata,
                "relevance_score": chunk.similarity_score,
                "source_title": chunk.metadata.get("title"),
                "source_type": chunk.metadata.get("source_type"),
                "source_id": chunk.knowledge_source_id
            })
        
        return formatted_results
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        strategy_id: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for content using keywords (hybrid search)."""
        
        # Get relevant knowledge sources for the strategy
        source_ids = self.knowledge_repo.get_source_ids_by_strategy(strategy_id)
        
        # Perform keyword search
        keyword_results = self.chunk_repo.keyword_search(
            keywords=keywords,
            source_ids=source_ids,
            limit=k
        )
        
        # Format results
        formatted_results = []
        for chunk in keyword_results:
            formatted_results.append({
                "content": chunk.content,
                "metadata": chunk.metadata,
                "relevance_score": chunk.rank_score,
                "source_title": chunk.metadata.get("title"),
                "source_type": chunk.metadata.get("source_type"),
                "source_id": chunk.knowledge_source_id
            })
        
        return formatted_results
    
    async def hybrid_search(
        self,
        query: str,
        strategy_id: str,
        k: int = 5,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Combine semantic and keyword search for better results."""
        
        # Get semantic results
        semantic_results = await self.retrieve_relevant_content(
            query=query,
            strategy_id=strategy_id,
            k=k * 2  # Get more for ranking
        )
        
        # Get keyword results
        keywords = query.split()  # Simple keyword extraction
        keyword_results = await self.search_by_keywords(
            keywords=keywords,
            strategy_id=strategy_id,
            k=k * 2
        )
        
        # Combine and rank results
        combined_results = self._combine_search_results(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            semantic_weight=semantic_weight
        )
        
        return combined_results[:k]
    
    def _combine_search_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Combine semantic and keyword search results with weighted scoring."""
        
        # Create a map of content to combined scores
        content_scores = {}
        
        # Add semantic scores
        for result in semantic_results:
            content_key = result["content"][:100]  # Use first 100 chars as key
            content_scores[content_key] = {
                "result": result,
                "semantic_score": result["relevance_score"],
                "keyword_score": 0.0
            }
        
        # Add keyword scores
        for result in keyword_results:
            content_key = result["content"][:100]
            if content_key in content_scores:
                content_scores[content_key]["keyword_score"] = result["relevance_score"]
            else:
                content_scores[content_key] = {
                    "result": result,
                    "semantic_score": 0.0,
                    "keyword_score": result["relevance_score"]
                }
        
        # Calculate combined scores and sort
        combined_results = []
        for content_data in content_scores.values():
            combined_score = (
                semantic_weight * content_data["semantic_score"] +
                (1 - semantic_weight) * content_data["keyword_score"]
            )
            
            result = content_data["result"].copy()
            result["combined_score"] = combined_score
            combined_results.append(result)
        
        # Sort by combined score (descending)
        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return combined_results
    
    def _load_document_content(self, knowledge_source: KnowledgeSource):
        """Load content from various document types."""
        
        if knowledge_source.content_type == "application/pdf":
            loader = PyPDFLoader(knowledge_source.storage_path)
        elif knowledge_source.content_type == "text/plain":
            loader = TextLoader(knowledge_source.storage_path)
        else:
            # For direct content
            from langchain.schema import Document
            return [Document(
                page_content=knowledge_source.content,
                metadata={"source": "direct"}
            )]
        
        return loader.load()
```

### 6. API Endpoints

```python
# app/api/v1/chat_sessions.py
@router.post("/sessions", response_model=ChatSessionResponse)
def start_chat_session(
    request: StartChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new chat session."""
    chat_engine = ChatEngineService(db)
    
    session = chat_engine.start_chat_session(
        strategy_id=request.strategy_id,
        patient_id=request.patient_id,
        session_type=request.session_type
    )
    
    return ChatSessionResponse.from_orm(session)

@router.post("/sessions/{session_id}/message", response_model=ChatMessageResponse)
def send_message(
    session_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send a message to the chat session."""
    chat_engine = ChatEngineService(db)
    
    response = chat_engine.process_patient_response(
        session_id=session_id,
        user_message=request.message
    )
    
    return ChatMessageResponse.from_orm(response)

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get chat session details."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ChatSessionResponse.from_orm(session)

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_chat_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages for a chat session."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()
    
    return [ChatMessageResponse.from_orm(msg) for msg in messages]
```

### 7. Schemas

```python
# app/schemas/chat_sessions.py
class StartChatRequest(BaseModel):
    strategy_id: str
    patient_id: str
    session_type: SessionType = SessionType.SCREENING

class SendMessageRequest(BaseModel):
    message: str

class ChatSessionResponse(BaseModel):
    id: str
    strategy_id: str
    patient_id: str
    session_type: SessionType
    status: SessionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    last_activity: datetime
    
    # Context
    chat_context: Optional[Dict[str, Any]]
    extracted_data: Optional[Dict[str, Any]]
    assessment_results: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    message_type: MessageType
    created_at: datetime
    confidence_score: Optional[float]
    extracted_entities: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True
```

## Integration Points

### 1. Knowledge Source Processing Pipeline

```python
# app/services/knowledge_processing.py
class KnowledgeProcessingService:
    """Process and index uploaded knowledge sources."""
    
    async def process_uploaded_file(self, knowledge_source: KnowledgeSource):
        """Process uploaded file for RAG integration."""
        try:
            # 1. Extract text content
            content = await self._extract_content(knowledge_source)
            
            # 2. Validate medical content
            validation_result = await self._validate_medical_content(content)
            
            # 3. Index for RAG
            rag_service = RAGService(self.db)
            await rag_service.index_knowledge_source(knowledge_source)
            
            # 4. Update processing status
            knowledge_source.processing_status = ProcessingStatus.COMPLETED
            
        except Exception as e:
            knowledge_source.processing_status = ProcessingStatus.FAILED
            knowledge_source.error_message = str(e)
            
        finally:
            self.db.commit()
```

### 2. External Tool Integration

```python
# app/services/external_tools.py
class ExternalToolsService:
    """Integration with external medical tools and calculators."""
    
    def calculate_risk_score(self, model_type: str, patient_data: Dict):
        """Calculate risk scores using external services."""
        
        if model_type == "tyrer_cuzick":
            return self._call_tyrer_cuzick_api(patient_data)
        elif model_type == "gail_model":
            return self._call_gail_model_api(patient_data)
        
    def _call_tyrer_cuzick_api(self, data: Dict) -> float:
        """Call external Tyrer-Cuzick calculator."""
        # Implementation would call actual external service
        pass
```

## Security and Compliance

### 1. HIPAA Compliance

```python
# app/core/hipaa_compliance.py
class HIPAAComplianceService:
    """Ensure HIPAA compliance for chat data."""
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PHI before storage."""
        
    def audit_data_access(self, user_id: str, data_type: str, action: str):
        """Log data access for compliance auditing."""
        
    def anonymize_for_ai(self, content: str) -> str:
        """Remove/anonymize PHI before sending to LLM."""
```

### 2. Data Privacy

```python
# app/core/privacy.py
class PrivacyService:
    """Handle data privacy and anonymization."""
    
    def anonymize_chat_content(self, message: str) -> str:
        """Remove PII from chat messages before AI processing."""
        
        # Remove names, dates, specific locations
        anonymized = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', message)
        anonymized = re.sub(r'\d{1,2}/\d{1,2}/\d{4}', '[DATE]', anonymized)
        
        return anonymized
```

## Performance and Scalability

### 1. Caching Strategy

```python
# app/core/caching.py
import redis
from typing import Optional

class ChatCacheService:
    """Caching for chat sessions and AI responses."""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def cache_session_context(self, session_id: str, context: Dict):
        """Cache session context for fast retrieval."""
        
    def get_cached_ai_response(self, prompt_hash: str) -> Optional[str]:
        """Get cached AI response for identical prompts."""
        
    def cache_rag_results(self, query_hash: str, results: List[Dict]):
        """Cache RAG retrieval results."""
```

### 2. Async Processing

```python
# app/services/async_processing.py
from celery import Celery

celery_app = Celery('chat_processing')

@celery_app.task
def process_knowledge_source_async(knowledge_source_id: str):
    """Process knowledge source in background."""
    
@celery_app.task
def generate_ai_response_async(session_id: str, message: str):
    """Generate AI response asynchronously."""
```

## Monitoring and Analytics

### 1. Chat Analytics

```python
# app/services/chat_analytics.py
class ChatAnalyticsService:
    """Analytics for chat performance and outcomes."""
    
    def track_conversation_metrics(self, session: ChatSession):
        """Track conversation length, completion rate, etc."""
        
    def analyze_extraction_accuracy(self, session: ChatSession):
        """Analyze how accurately information was extracted."""
        
    def generate_clinician_insights(self, strategy_id: str):
        """Generate insights for clinicians about chat effectiveness."""
```

## Deployment Configuration

### 1. Environment Variables

```bash
# AI and LLM Configuration
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=...
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Database Configuration (with pgvector)
DATABASE_URL=postgresql://user:pass@localhost:5432/genascope
PGVECTOR_EXTENSION_ENABLED=true

# External Tools
TYRER_CUZICK_API_URL=https://api.tcrisk.com
GAIL_MODEL_API_URL=https://api.gailmodel.com

# Caching
REDIS_URL=redis://localhost:6379/0

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.7
MAX_RETRIEVAL_RESULTS=5

# Monitoring
SENTRY_DSN=https://...
DATADOG_API_KEY=...
```

### 2. Database Migration for pgvector

The system requires the pgvector extension to be installed in PostgreSQL:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create indexes for optimal performance
CREATE INDEX CONCURRENTLY ix_document_chunks_embedding_cosine 
ON document_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX CONCURRENTLY ix_document_chunks_content_fts 
ON document_chunks USING gin (to_tsvector('english', content));
```

This comprehensive design provides a robust, scalable, and compliant AI-driven chat system that can adapt to various medical screening scenarios while maintaining high standards for privacy, security, and clinical accuracy.
