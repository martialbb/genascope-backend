# AI Chat Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the AI-driven chat system in the GenAScope backend following a layered architecture pattern. The implementation builds on the existing chat configuration infrastructure and adds intelligent conversation capabilities.

## Architecture Overview

The implementation follows a clear separation of concerns with three distinct layers:

```
┌─────────────────┐
│   API Layer     │  ← FastAPI endpoints, request/response handling
│                 │
├─────────────────┤
│  Service Layer  │  ← Business logic, AI orchestration, workflow management
│                 │
├─────────────────┤
│Repository Layer │  ← Data access, database operations, query logic
│                 │
└─────────────────┘
│   Database      │  ← PostgreSQL with SQLAlchemy models
└─────────────────┘
```

**Data Flow**: `API → Service → Repository → Database`

- **API Layer** (`app/api/`): Handles HTTP requests, validates input, calls service layer
- **Service Layer** (`app/services/`): Contains business logic, coordinates between repositories, manages AI workflows
- **Repository Layer** (`app/repositories/`): Encapsulates all database access, provides clean data interface
- **Database Layer**: PostgreSQL with SQLAlchemy models

This architecture ensures:
- **Clean separation of concerns**: Each layer has a single responsibility
- **Testability**: Each layer can be mocked and tested independently
- **Maintainability**: Changes to database schema only affect repository layer
- **Scalability**: Business logic is decoupled from data access patterns

## Prerequisites

1. **Existing Infrastructure**: Chat configuration system is already implemented
2. **Database**: PostgreSQL with existing chat strategy tables
3. **Dependencies**: Python 3.8+, FastAPI, SQLAlchemy, LangChain

## Implementation Steps

### Step 1: Install Dependencies

```bash
# Install AI chat dependencies
pip install -r requirements.ai-chat.txt

# Install pgvector Python client
pip install pgvector

# Download spaCy model
python -m spacy download en_core_web_sm
```

Update `requirements.ai-chat.txt` to include pgvector:

```txt
# AI and LLM dependencies
openai>=1.0.0
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-community>=0.1.0

# Vector database
pgvector>=0.2.0
psycopg2-binary>=2.9.0

# Text processing
spacy>=3.6.0
pypdf>=3.15.0

# Background processing
celery>=5.3.0
redis>=4.6.0

# Monitoring and observability
sentry-sdk>=1.32.0
prometheus-client>=0.17.0
```

### Step 2: Database Migration

```bash
# Run the AI chat migration
alembic upgrade head
```

This will create the following tables:
- `chat_sessions` - AI chat sessions
- `chat_messages` - Individual messages
- `extraction_rules` - Information extraction rules
- `session_analytics` - Performance metrics
- `document_chunks` - Document chunks with vector embeddings (pgvector)

### Step 2.1: pgvector Setup

Ensure pgvector extension is installed in your PostgreSQL database:

```sql
-- Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

Create a new migration for document chunks:

```bash
# Create migration for document chunks with pgvector
alembic revision --autogenerate -m "add_document_chunks_with_pgvector"
```

Example migration content (`alembic/versions/014_document_chunks.py`):

```python
"""add document chunks with pgvector

Revision ID: 014_document_chunks
Revises: 013_ai_chat_sessions
Create Date: 2025-07-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = '014_document_chunks'
down_revision = '013_ai_chat_sessions'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_source_id'], ['knowledge_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_document_chunks_knowledge_source', 'document_chunks', ['knowledge_source_id'])
    op.create_index('ix_document_chunks_content_fts', 'document_chunks', 
                   [sa.text("to_tsvector('english', content)")], postgresql_using='gin')
    
    # Create vector similarity index (requires pgvector)
    op.execute("CREATE INDEX ix_document_chunks_embedding_cosine ON document_chunks USING ivfflat (embedding vector_cosine_ops)")

def downgrade() -> None:
    op.drop_table('document_chunks')
```

### Step 3: Environment Configuration

Add the following to your `.env.local` file:

```bash
# AI Configuration
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=500

# LangChain (optional for tracing)
LANGCHAIN_API_KEY=your-langchain-key
LANGCHAIN_PROJECT=genascope-chat
LANGCHAIN_TRACING_V2=true

# Vector Embeddings (pgvector)
PGVECTOR_EXTENSION_ENABLED=true
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.7

# Chat Configuration
MAX_CONVERSATION_TURNS=20
SESSION_TIMEOUT_HOURS=24
MAX_MESSAGE_LENGTH=2000

# Security
ANONYMIZE_BEFORE_AI=true
MASK_PII=true
ENABLE_AUDIT_LOGGING=true

# Caching
REDIS_URL=redis://localhost:6379/0
ENABLE_RESPONSE_CACHING=true
RESPONSE_CACHE_TTL=3600

# External Tools
ENABLE_MOCK_CALCULATORS=true
TYRER_CUZICK_API_URL=https://api.tcrisk.com
```

### Step 4: Core Service Implementation

#### 4.1 Update Main Application

Add to `app/main.py`:

```python
from app.api.v1.chat_sessions import router as chat_sessions_router
from app.services.knowledge_processing import KnowledgeProcessingService
from app.core.ai_chat_config import ai_chat_settings

# Add router
app.include_router(chat_sessions_router, prefix="/api/v1", tags=["AI Chat"])

# Initialize AI services on startup
@app.on_event("startup")
async def startup_event():
    # Initialize pgvector extension
    from app.db.database import engine
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Initialize RAG service with pgvector
    from app.services.rag_service import RAGService
    rag_service = RAGService(next(get_db()))
    
    # Initialize knowledge processing
    knowledge_service = KnowledgeProcessingService(next(get_db()))
    
    # Process any pending knowledge sources
    await knowledge_service.process_pending_sources()
```

#### 4.2 Create API Endpoints

Create `app/api/v1/chat_sessions.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.services.chat_engine import ChatEngineService
from app.schemas.ai_chat import (
    StartChatRequest, SendMessageRequest, ChatSessionResponse,
    ChatMessageResponse, ChatSessionListRequest, ChatSessionListResponse
)

router = APIRouter(prefix="/chat", tags=["AI Chat Sessions"])

@router.post("/sessions", response_model=ChatSessionResponse)
async def start_chat_session(
    request: StartChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new AI chat session.
    
    Flow: API → ChatEngineService → ChatSessionRepository/ChatMessageRepository → Database
    """
    # Service layer handles business logic and calls repositories
    chat_engine = ChatEngineService(db)
    
    # Validate strategy exists and user has access
    strategy = chat_engine.validate_strategy_access(
        request.strategy_id, 
        current_user.account_id
    )
    
    # Start session (service → repository → database)
    session = await chat_engine.start_chat_session(
        strategy_id=request.strategy_id,
        patient_id=request.patient_id,
        session_type=request.session_type,
        initial_context=request.initial_context
    )
    
    # Process initial setup in background
    background_tasks.add_task(
        chat_engine.setup_session_context, 
        session.id
    )
    
    return ChatSessionResponse.from_orm(session)

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send a message to the AI chat session.
    
    Flow: API → ChatEngineService → Multiple Repositories → Database
    """
    # Service layer orchestrates the conversation flow via repositories
    chat_engine = ChatEngineService(db)
    
    # Validate session access
    session = chat_engine.validate_session_access(session_id, current_user)
    
    # Process message and generate response (service → repositories → database)
    response = await chat_engine.process_patient_response(
        session_id=session_id,
        user_message=request.message,
        metadata=request.message_metadata
    )
    
    return ChatMessageResponse.from_orm(response)

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get chat session details.
    
    Flow: API → ChatEngineService → ChatSessionRepository → Database
    """
    chat_engine = ChatEngineService(db)
    session = chat_engine.validate_session_access(session_id, current_user)
    
    return ChatSessionResponse.from_orm(session)

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages for a chat session.
    
    Flow: API → ChatEngineService → ChatMessageRepository → Database
    """
    chat_engine = ChatEngineService(db)
    session = chat_engine.validate_session_access(session_id, current_user)
    
    # Service calls repository for data access
    messages = chat_engine.get_session_messages(session_id, skip, limit)
    return [ChatMessageResponse.from_orm(msg) for msg in messages]

@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    request: ChatSessionListRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List chat sessions for the current user.
    
    Flow: API → ChatEngineService → ChatSessionRepository → Database
    """
    chat_engine = ChatEngineService(db)
    
    # Service calls repository for filtered data access
    sessions, total_count = chat_engine.list_sessions(
        account_id=current_user.account_id,
        filters=request,
        skip=request.skip,
        limit=request.limit
    )
    
    return ChatSessionListResponse(
        sessions=[ChatSessionResponse.from_orm(s) for s in sessions],
        total_count=total_count,
        skip=request.skip,
        limit=request.limit
    )
```

### Step 5: Repository Layer Implementation

Following the layered architecture (API → Service → Repository → Database), implement the repository layer first:

1. **Chat Session Repository** (`app/repositories/chat_session_repository.py`) - Database operations for chat sessions
2. **Chat Message Repository** (`app/repositories/chat_message_repository.py`) - Database operations for messages
3. **Extraction Rule Repository** (`app/repositories/extraction_rule_repository.py`) - Database operations for extraction rules
4. **Analytics Repository** (`app/repositories/analytics_repository.py`) - Database operations for analytics

Create `app/repositories/chat_session_repository.py`:

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.ai_chat import ChatSession, SessionStatus, SessionType
from app.schemas.ai_chat import ChatSessionCreate, ChatSessionUpdate

class ChatSessionRepository:
    """Repository for chat session database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """Create a new chat session."""
        db_session = ChatSession(**session_data.dict())
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session
    
    def get_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
    
    def update_session(self, session_id: str, updates: ChatSessionUpdate) -> Optional[ChatSession]:
        """Update a chat session."""
        session = self.get_session_by_id(session_id)
        if session:
            for field, value in updates.dict(exclude_unset=True).items():
                setattr(session, field, value)
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def list_sessions_by_account(
        self, 
        account_id: str, 
        status: Optional[SessionStatus] = None,
        skip: int = 0, 
        limit: int = 50
    ) -> tuple[List[ChatSession], int]:
        """List chat sessions for an account with pagination."""
        query = self.db.query(ChatSession).filter(
            ChatSession.account_id == account_id
        )
        
        if status:
            query = query.filter(ChatSession.status == status)
        
        total_count = query.count()
        sessions = query.order_by(desc(ChatSession.created_at)).offset(skip).limit(limit).all()
        
        return sessions, total_count
    
    def get_sessions_by_patient(self, patient_id: str) -> List[ChatSession]:
        """Get all sessions for a specific patient."""
        return self.db.query(ChatSession).filter(
            ChatSession.patient_id == patient_id
        ).order_by(desc(ChatSession.created_at)).all()
```

Create `app/repositories/chat_message_repository.py`:

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.ai_chat import ChatMessage, MessageRole
from app.schemas.ai_chat import ChatMessageCreate

class ChatMessageRepository:
    """Repository for chat message database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """Create a new chat message."""
        db_message = ChatMessage(**message_data.dict())
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message
    
    def get_session_messages(
        self, 
        session_id: str, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get messages for a chat session with pagination."""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).offset(skip).limit(limit).all()
    
    def get_latest_message(self, session_id: str) -> Optional[ChatMessage]:
        """Get the latest message in a session."""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.timestamp)).first()
    
    def count_messages_by_role(self, session_id: str, role: MessageRole) -> int:
        """Count messages by role in a session."""
        return self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.role == role
            )
        ).count()

class DocumentChunkRepository:
    """Repository for document chunk operations with pgvector."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document_chunk(self, chunk_data: dict) -> DocumentChunk:
        """Create a new document chunk with embedding."""
        from app.models.ai_chat import DocumentChunk
        
        chunk = DocumentChunk(
            knowledge_source_id=chunk_data["knowledge_source_id"],
            content=chunk_data["content"],
            embedding=chunk_data["embedding"],
            chunk_index=chunk_data["chunk_index"],
            metadata=chunk_data["metadata"]
        )
        
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk
    
    def similarity_search(
        self,
        query_embedding: List[float],
        source_ids: List[str],
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[dict]:
        """Perform similarity search using pgvector."""
        from app.models.ai_chat import DocumentChunk
        from sqlalchemy import text
        
        # Convert query embedding to pgvector format
        query_vector = f"[{','.join(map(str, query_embedding))}]"
        
        # Perform cosine similarity search
        query = text("""
            SELECT 
                id, knowledge_source_id, content, chunk_index, metadata, created_at,
                (1 - (embedding <=> :query_vector)) as similarity_score
            FROM document_chunks 
            WHERE knowledge_source_id = ANY(:source_ids)
            AND (1 - (embedding <=> :query_vector)) >= :threshold
            ORDER BY embedding <=> :query_vector
            LIMIT :limit
        """)
        
        results = self.db.execute(query, {
            "query_vector": query_vector,
            "source_ids": source_ids,
            "threshold": similarity_threshold,
            "limit": limit
        }).fetchall()
        
        # Convert to dictionaries
        return [dict(row._mapping) for row in results]
    
    def keyword_search(
        self,
        keywords: List[str],
        source_ids: List[str],
        limit: int = 5
    ) -> List[dict]:
        """Perform full-text search using PostgreSQL."""
        from app.models.ai_chat import DocumentChunk
        from sqlalchemy import text, func
        
        # Create tsquery from keywords
        search_query = " & ".join(keywords)
        
        query = text("""
            SELECT 
                id, knowledge_source_id, content, chunk_index, metadata, created_at,
                ts_rank(to_tsvector('english', content), to_tsquery('english', :search_query)) as rank_score
            FROM document_chunks 
            WHERE knowledge_source_id = ANY(:source_ids)
            AND to_tsvector('english', content) @@ to_tsquery('english', :search_query)
            ORDER BY ts_rank(to_tsvector('english', content), to_tsquery('english', :search_query)) DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, {
            "search_query": search_query,
            "source_ids": source_ids,
            "limit": limit
        }).fetchall()
        
        return [dict(row._mapping) for row in results]
    
    def get_chunks_by_source(self, source_id: str) -> List[DocumentChunk]:
        """Get all chunks for a knowledge source."""
        from app.models.ai_chat import DocumentChunk
        
        return self.db.query(DocumentChunk).filter(
            DocumentChunk.knowledge_source_id == source_id
        ).order_by(DocumentChunk.chunk_index).all()
    
    def delete_chunks_by_source(self, source_id: str) -> int:
        """Delete all chunks for a knowledge source."""
        from app.models.ai_chat import DocumentChunk
        
        deleted_count = self.db.query(DocumentChunk).filter(
            DocumentChunk.knowledge_source_id == source_id
        ).delete()
        self.db.commit()
        return deleted_count
```

### Step 6: Service Layer Implementation

Now implement the service layer that calls the repository layer:

1. **RAG Service** (`app/services/rag_service.py`) - For knowledge retrieval
2. **Entity Extraction** (`app/services/entity_extraction.py`) - For information extraction
3. **Criteria Assessment** (`app/services/criteria_assessment.py`) - For patient assessment
4. **Chat Engine** (`app/services/chat_engine.py`) - Main conversation orchestrator

Update `app/services/chat_engine.py` to use repositories:

```python
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.extraction_rule_repository import ExtractionRuleRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository

class ChatEngineService:
    """Main service for orchestrating AI chat conversations."""
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize repositories
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = ChatMessageRepository(db)
        self.extraction_repo = ExtractionRuleRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        self.chunk_repo = DocumentChunkRepository(db)
        
        # Initialize other services
        self.rag_service = RAGService(db)
        self.extraction_service = EntityExtractionService(db)
        self.assessment_service = CriteriaAssessmentService(db)
    
    async def start_chat_session(
        self, 
        strategy_id: str, 
        patient_id: str, 
        session_type: SessionType,
        initial_context: Optional[dict] = None
    ) -> ChatSession:
        """Start a new chat session using repository layer."""
        
        # Create session via repository
        session_data = ChatSessionCreate(
            strategy_id=strategy_id,
            patient_id=patient_id,
            session_type=session_type,
            status=SessionStatus.ACTIVE,
            chat_context=initial_context or {},
            extracted_data={},
            assessment_results={}
        )
        
        session = self.session_repo.create_session(session_data)
        
        # Create initial assistant message via repository
        welcome_message = ChatMessageCreate(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=self._generate_welcome_message(strategy_id),
            message_metadata={"type": "welcome"}
        )
        
        self.message_repo.create_message(welcome_message)
        
        return session
    
    async def process_patient_response(
        self, 
        session_id: str, 
        user_message: str,
        metadata: Optional[dict] = None
    ) -> ChatMessage:
        """Process patient response using repository layer."""
        
        # Get session via repository
        session = self.session_repo.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Create user message via repository
        user_msg_data = ChatMessageCreate(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
            message_metadata=metadata or {}
        )
        
        user_msg = self.message_repo.create_message(user_msg_data)
        
        # Extract entities and update session context
        extracted_data = await self.extraction_service.extract_entities(
            user_message, session.chat_context
        )
        
        # Update session with extracted data via repository
        session_updates = ChatSessionUpdate(
            extracted_data={**session.extracted_data, **extracted_data}
        )
        
        self.session_repo.update_session(session_id, session_updates)
        
        # Generate AI response
        ai_response = await self._generate_ai_response(session, user_message)
        
        # Create assistant message via repository
        assistant_msg_data = ChatMessageCreate(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response["content"],
            message_metadata=ai_response.get("metadata", {})
        )
        
        return self.message_repo.create_message(assistant_msg_data)
```

### Step 7: Knowledge Source Integration

Update the existing knowledge source processing to include RAG indexing, following the repository pattern:

```python
# In app/services/chat_configuration_sync.py

class ChatConfigurationSyncService:
    """Service for syncing chat configuration, using repository layer."""
    
    def __init__(self, db: Session):
        self.db = db
        # Use existing repositories from chat_configuration.py
        from app.repositories.chat_configuration import KnowledgeSourceRepository
        self.knowledge_repo = KnowledgeSourceRepository(db)
        self.rag_service = RAGService(db)
    
    async def upload_file(self, file: UploadFile, request: FileUploadRequest, ...):
        # ... existing upload logic using repository ...
        
        # Create knowledge source via existing repository
        knowledge_source = self.knowledge_repo.create(source_data)
        
        # Process and update status via existing repository
        if knowledge_source.processing_status == ProcessingStatus.COMPLETED:
            # Add RAG indexing in background
            background_tasks.add_task(
                self.rag_service.index_knowledge_source,
                knowledge_source
            )
            
            # Update status via existing repository
            self.knowledge_repo.update(
                knowledge_source.id, 
                {"processing_status": ProcessingStatus.INDEXED}
            )
```

**Note**: The `KnowledgeSourceRepository` already exists in `app/repositories/chat_configuration.py` with methods like `create()`, `get_by_id()`, `update()`, etc., so we reuse the existing repository instead of creating a duplicate.

### Step 8: Configuration Templates

Create strategy templates for common scenarios, following the repository pattern:

```python
# In app/services/strategy_templates.py

class StrategyTemplateService:
    """Service for creating pre-configured strategy templates."""
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize repositories
        self.strategy_repo = ChatStrategyRepository(db)
        self.knowledge_repo = KnowledgeSourceRepository(db)
    
    def create_breast_cancer_screening_strategy(self, account_id: str, user_id: str):
        """Create a pre-configured breast cancer screening strategy.
        
        Flow: Service → ChatStrategyRepository → Database
        """
        from app.core.ai_chat_config import BREAST_CANCER_SCREENING_CONFIG
        
        strategy_data = ChatStrategyCreate(
            name=BREAST_CANCER_SCREENING_CONFIG["strategy_name"],
            description="AI-driven breast cancer risk assessment",
            specialty="Oncology",
            goal="Assess breast cancer risk and determine genetic testing eligibility",
            patient_introduction="I'll help assess your breast cancer risk through a brief conversation.",
            knowledge_source_ids=[],  # Add relevant knowledge sources
            targeting_rules=[],
            outcome_actions=[],
            ai_model_config=BREAST_CANCER_SCREENING_CONFIG["ai_model_config"],
            extraction_rules=BREAST_CANCER_SCREENING_CONFIG["extraction_rules"],
            assessment_criteria=BREAST_CANCER_SCREENING_CONFIG["assessment_criteria"]
        )
        
        # Create strategy using existing repository
        return self.strategy_repo.create(strategy_data, user_id, account_id)
    
    def get_available_templates(self) -> List[dict]:
        """Get list of available strategy templates."""
        return [
            {
                "template_id": "breast_cancer_screening",
                "name": "Breast Cancer Risk Assessment",
                "description": "AI-driven conversation for breast cancer risk assessment",
                "specialty": "Oncology"
            },
            {
                "template_id": "genetic_counseling_intake",
                "name": "Genetic Counseling Intake",
                "description": "Structured intake for genetic counseling services",
                "specialty": "Genetics"
            }
        ]
```

**Note**: The `ChatStrategyRepository` and `KnowledgeSourceRepository` already exist in `app/repositories/chat_configuration.py`, so we reuse them instead of creating duplicates. The existing repositories provide all the necessary methods for chat strategy and knowledge source management.

### Step 9: Testing Implementation

Comprehensive testing ensures the AI chat system works correctly across all layers. Following the layered architecture, we test each component in isolation and integration.

#### 9.1 Repository Layer Tests

Test the data access layer with database operations:

Create `app/tests/repositories/test_chat_session_repository.py`:

```python
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from app.repositories.chat_session_repository import ChatSessionRepository
from app.models.ai_chat import ChatSession, SessionStatus, SessionType
from app.schemas.ai_chat import ChatSessionCreate, ChatSessionUpdate

@pytest.fixture
def db_session():
    """Mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def chat_session_repo(db_session):
    """Chat session repository fixture."""
    return ChatSessionRepository(db_session)

@pytest.fixture
def sample_session():
    """Sample chat session for testing."""
    return ChatSession(
        id="test-session-123",
        strategy_id="strategy-456",
        patient_id="patient-789",
        session_type=SessionType.INTAKE,
        status=SessionStatus.ACTIVE,
        chat_context={"specialty": "oncology"},
        extracted_data={"age": 45},
        assessment_results={}
    )

class TestChatSessionRepository:
    """Test cases for ChatSessionRepository."""
    
    def test_create_session(self, chat_session_repo, db_session):
        """Test creating a new chat session."""
        session_data = ChatSessionCreate(
            strategy_id="strategy-456",
            patient_id="patient-789",
            session_type=SessionType.INTAKE,
            status=SessionStatus.ACTIVE,
            chat_context={"specialty": "oncology"},
            extracted_data={},
            assessment_results={}
        )
        
        # Mock database operations
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()
        
        # Create session
        result = chat_session_repo.create_session(session_data)
        
        # Verify database calls
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
        
        assert result.strategy_id == "strategy-456"
        assert result.patient_id == "patient-789"
        assert result.session_type == SessionType.INTAKE
    
    def test_get_session_by_id(self, chat_session_repo, db_session, sample_session):
        """Test retrieving a session by ID."""
        # Mock query chain
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = sample_session
        db_session.query.return_value = query_mock
        
        result = chat_session_repo.get_session_by_id("test-session-123")
        
        # Verify query was called correctly
        db_session.query.assert_called_once_with(ChatSession)
        query_mock.filter.assert_called_once()
        filter_mock.first.assert_called_once()
        
        assert result == sample_session
    
    def test_list_sessions_by_account(self, chat_session_repo, db_session, sample_session):
        """Test listing sessions for an account with pagination."""
        # Mock query chain
        query_mock = Mock()
        filter_mock = Mock()
        order_mock = Mock()
        offset_mock = Mock()
        limit_mock = Mock()
        
        query_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value = order_mock
        order_mock.offset.return_value = offset_mock
        offset_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = [sample_session]
        
        db_session.query.return_value = query_mock
        
        sessions, total_count = chat_session_repo.list_sessions_by_account(
            "account-123", skip=0, limit=10
        )
        
        # Verify query chain
        assert total_count == 1
        assert len(sessions) == 1
        assert sessions[0] == sample_session
```

Create `app/tests/repositories/test_document_chunk_repository.py`:

```python
import pytest
from unittest.mock import Mock, patch
from app.repositories.chat_message_repository import DocumentChunkRepository
from app.models.ai_chat import DocumentChunk

@pytest.fixture
def chunk_repo(db_session):
    """Document chunk repository fixture."""
    return DocumentChunkRepository(db_session)

@pytest.fixture
def sample_embedding():
    """Sample embedding vector."""
    return [0.1, 0.2, 0.3, 0.4, 0.5] * 307 + [0.1]  # 1536 dimensions

class TestDocumentChunkRepository:
    """Test cases for DocumentChunkRepository with pgvector."""
    
    def test_create_document_chunk(self, chunk_repo, db_session, sample_embedding):
        """Test creating a document chunk with embedding."""
        chunk_data = {
            "knowledge_source_id": "source-123",
            "content": "This is a test document chunk.",
            "embedding": sample_embedding,
            "chunk_index": 0,
            "metadata": {"page": 1, "source": "test.pdf"}
        }
        
        # Mock database operations
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()
        
        result = chunk_repo.create_document_chunk(chunk_data)
        
        # Verify database calls
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
        
        assert result.knowledge_source_id == "source-123"
        assert result.content == "This is a test document chunk."
        assert result.chunk_index == 0
    
    def test_similarity_search(self, chunk_repo, db_session, sample_embedding):
        """Test pgvector similarity search."""
        # Mock database execute
        result_mock = Mock()
        result_mock._mapping = {
            "id": "chunk-123",
            "knowledge_source_id": "source-123",
            "content": "Similar content",
            "similarity_score": 0.85
        }
        
        execute_mock = Mock()
        execute_mock.fetchall.return_value = [result_mock]
        db_session.execute.return_value = execute_mock
        
        results = chunk_repo.similarity_search(
            query_embedding=sample_embedding,
            source_ids=["source-123"],
            limit=5,
            similarity_threshold=0.7
        )
        
        # Verify SQL execution
        db_session.execute.assert_called_once()
        execute_mock.fetchall.assert_called_once()
        
        assert len(results) == 1
        assert results[0]["similarity_score"] == 0.85
        assert results[0]["content"] == "Similar content"
    
    def test_keyword_search(self, chunk_repo, db_session):
        """Test PostgreSQL full-text search."""
        # Mock database execute
        result_mock = Mock()
        result_mock._mapping = {
            "id": "chunk-456",
            "knowledge_source_id": "source-123",
            "content": "Breast cancer risk assessment",
            "rank_score": 0.95
        }
        
        execute_mock = Mock()
        execute_mock.fetchall.return_value = [result_mock]
        db_session.execute.return_value = execute_mock
        
        results = chunk_repo.keyword_search(
            keywords=["breast", "cancer"],
            source_ids=["source-123"],
            limit=5
        )
        
        # Verify SQL execution
        db_session.execute.assert_called_once()
        execute_mock.fetchall.assert_called_once()
        
        assert len(results) == 1
        assert results[0]["rank_score"] == 0.95
        assert "breast cancer" in results[0]["content"].lower()
```

#### 9.2 Service Layer Tests

Test business logic and service orchestration:

Create `app/tests/services/test_chat_engine.py`:

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.chat_engine import ChatEngineService
from app.models.ai_chat import ChatSession, ChatMessage, SessionType, SessionStatus, MessageRole
from app.schemas.ai_chat import ChatSessionCreate

@pytest.fixture
def mock_repositories():
    """Mock all repositories used by ChatEngineService."""
    return {
        'session_repo': Mock(),
        'message_repo': Mock(),
        'extraction_repo': Mock(),
        'analytics_repo': Mock(),
        'chunk_repo': Mock()
    }

@pytest.fixture
def chat_engine(db_session, mock_repositories):
    """ChatEngineService with mocked repositories."""
    service = ChatEngineService(db_session)
    
    # Replace repositories with mocks
    for repo_name, mock_repo in mock_repositories.items():
        setattr(service, repo_name, mock_repo)
    
    # Mock other services
    service.rag_service = Mock()
    service.extraction_service = Mock()
    service.assessment_service = Mock()
    
    return service

class TestChatEngineService:
    """Test cases for ChatEngineService."""
    
    @pytest.mark.asyncio
    async def test_start_chat_session(self, chat_engine, mock_repositories):
        """Test starting a new chat session."""
        # Mock repository returns
        mock_session = ChatSession(
            id="session-123",
            strategy_id="strategy-456",
            patient_id="patient-789",
            session_type=SessionType.INTAKE,
            status=SessionStatus.ACTIVE
        )
        
        mock_message = ChatMessage(
            id="msg-123",
            session_id="session-123",
            role=MessageRole.ASSISTANT,
            content="Welcome to the assessment"
        )
        
        mock_repositories['session_repo'].create_session.return_value = mock_session
        mock_repositories['message_repo'].create_message.return_value = mock_message
        
        # Start session
        result = await chat_engine.start_chat_session(
            strategy_id="strategy-456",
            patient_id="patient-789",
            session_type=SessionType.INTAKE
        )
        
        # Verify repository calls
        mock_repositories['session_repo'].create_session.assert_called_once()
        mock_repositories['message_repo'].create_message.assert_called_once()
        
        assert result.id == "session-123"
        assert result.strategy_id == "strategy-456"
        assert result.patient_id == "patient-789"
    
    @pytest.mark.asyncio
    async def test_process_patient_response(self, chat_engine, mock_repositories):
        """Test processing patient response with entity extraction."""
        # Mock existing session
        mock_session = ChatSession(
            id="session-123",
            strategy_id="strategy-456",
            patient_id="patient-789",
            chat_context={"specialty": "oncology"},
            extracted_data={"age": 45}
        )
        
        # Mock extraction service
        chat_engine.extraction_service.extract_entities = AsyncMock(
            return_value={"family_history": "positive"}
        )
        
        # Mock repository returns
        mock_repositories['session_repo'].get_session_by_id.return_value = mock_session
        mock_repositories['message_repo'].create_message.side_effect = [
            # User message
            ChatMessage(id="msg-user", role=MessageRole.USER, content="Yes, my mother had breast cancer"),
            # Assistant message
            ChatMessage(id="msg-assistant", role=MessageRole.ASSISTANT, content="Thank you for sharing that information")
        ]
        
        # Mock AI response generation
        chat_engine._generate_ai_response = AsyncMock(
            return_value={"content": "Thank you for sharing that information", "metadata": {}}
        )
        
        # Process response
        result = await chat_engine.process_patient_response(
            session_id="session-123",
            user_message="Yes, my mother had breast cancer"
        )
        
        # Verify service calls
        mock_repositories['session_repo'].get_session_by_id.assert_called_with("session-123")
        mock_repositories['session_repo'].update_session.assert_called_once()
        chat_engine.extraction_service.extract_entities.assert_called_once()
        
        assert result.role == MessageRole.ASSISTANT
        assert "Thank you" in result.content
```

Create `app/tests/services/test_rag_service.py`:

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.rag_service import RAGService

@pytest.fixture
def rag_service(db_session):
    """RAGService with mocked dependencies."""
    service = RAGService(db_session)
    service.chunk_repo = Mock()
    service.openai_client = Mock()
    return service

class TestRAGService:
    """Test cases for RAGService with pgvector."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, rag_service):
        """Test hybrid search combining vector and keyword search."""
        # Mock embeddings
        query_embedding = [0.1, 0.2, 0.3] * 512
        
        # Mock vector search results
        vector_results = [
            {"id": "chunk-1", "content": "Breast cancer risk factors", "similarity_score": 0.85},
            {"id": "chunk-2", "content": "BRCA gene mutations", "similarity_score": 0.80}
        ]
        
        # Mock keyword search results
        keyword_results = [
            {"id": "chunk-3", "content": "Family history assessment", "rank_score": 0.90},
            {"id": "chunk-1", "content": "Breast cancer risk factors", "rank_score": 0.75}
        ]
        
        rag_service.chunk_repo.similarity_search.return_value = vector_results
        rag_service.chunk_repo.keyword_search.return_value = keyword_results
        
        # Mock OpenAI embeddings
        rag_service.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=query_embedding)]
        )
        
        # Perform hybrid search
        results = await rag_service.hybrid_search(
            query="breast cancer risk factors",
            source_ids=["source-123"],
            limit=5
        )
        
        # Verify repository calls
        rag_service.chunk_repo.similarity_search.assert_called_once()
        rag_service.chunk_repo.keyword_search.assert_called_once()
        
        # Verify results are ranked and deduplicated
        assert len(results) >= 2
        assert all("content" in result for result in results)
        assert all("combined_score" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_generate_context_aware_response(self, rag_service):
        """Test generating context-aware AI responses."""
        # Mock retrieved context
        context_chunks = [
            {"content": "BRCA1 mutations increase breast cancer risk by 55-65%"},
            {"content": "Family history is a significant risk factor"}
        ]
        
        # Mock OpenAI chat completion
        rag_service.openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Based on the information, genetic testing may be recommended."))]
        )
        
        response = await rag_service.generate_context_aware_response(
            query="Should I get genetic testing?",
            context_chunks=context_chunks,
            chat_history=[],
            extracted_data={"family_history": "positive"}
        )
        
        # Verify OpenAI call
        rag_service.openai_client.chat.completions.create.assert_called_once()
        
        assert "genetic testing" in response.lower()
        assert len(response) > 0
```

#### 9.3 API Layer Tests

Test FastAPI endpoints and request/response handling:

Create `app/tests/api/test_chat_sessions.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from app.main import app
from app.api.auth import get_current_active_user
from app.db.database import get_db

@pytest.fixture
def test_client():
    """Test client for API endpoints."""
    return TestClient(app)

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return Mock(
        id="user-123",
        account_id="account-456",
        email="test@example.com",
        is_active=True
    )

@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()

@pytest.fixture(autouse=True)
def override_dependencies(mock_user, mock_db):
    """Override FastAPI dependencies for testing."""
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

class TestChatSessionsAPI:
    """Test cases for chat sessions API endpoints."""
    
    @patch('app.api.v1.chat_sessions.ChatEngineService')
    def test_start_chat_session(self, mock_chat_engine_class, test_client, mock_user):
        """Test starting a new chat session via API."""
        # Mock service
        mock_service = Mock()
        mock_service.validate_strategy_access.return_value = Mock(id="strategy-123")
        mock_service.start_chat_session = AsyncMock(return_value=Mock(
            id="session-456",
            strategy_id="strategy-123",
            patient_id="patient-789",
            session_type="intake",
            status="active"
        ))
        mock_chat_engine_class.return_value = mock_service
        
        # API request
        response = test_client.post(
            "/api/v1/chat/sessions",
            json={
                "strategy_id": "strategy-123",
                "patient_id": "patient-789",
                "session_type": "intake",
                "initial_context": {"specialty": "oncology"}
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-456"
        assert data["strategy_id"] == "strategy-123"
        assert data["patient_id"] == "patient-789"
        
        # Verify service calls
        mock_service.validate_strategy_access.assert_called_once_with("strategy-123", mock_user.account_id)
        mock_service.start_chat_session.assert_called_once()
    
    @patch('app.api.v1.chat_sessions.ChatEngineService')
    def test_send_message(self, mock_chat_engine_class, test_client, mock_user):
        """Test sending a message to a chat session."""
        # Mock service
        mock_service = Mock()
        mock_service.validate_session_access.return_value = Mock(id="session-123")
        mock_service.process_patient_response = AsyncMock(return_value=Mock(
            id="msg-456",
            session_id="session-123",
            role="assistant",
            content="Thank you for that information. Can you tell me more about your family history?"
        ))
        mock_chat_engine_class.return_value = mock_service
        
        # API request
        response = test_client.post(
            "/api/v1/chat/sessions/session-123/messages",
            json={
                "message": "I'm 45 years old",
                "message_metadata": {"type": "user_input"}
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "msg-456"
        assert data["role"] == "assistant"
        assert "family history" in data["content"]
        
        # Verify service calls
        mock_service.validate_session_access.assert_called_once_with("session-123", mock_user)
        mock_service.process_patient_response.assert_called_once()
    
    @patch('app.api.v1.chat_sessions.ChatEngineService')
    def test_get_chat_messages(self, mock_chat_engine_class, test_client, mock_user):
        """Test retrieving chat messages."""
        # Mock service
        mock_service = Mock()
        mock_service.validate_session_access.return_value = Mock(id="session-123")
        mock_service.get_session_messages.return_value = [
            Mock(id="msg-1", role="assistant", content="Hello", timestamp="2025-07-02T10:00:00"),
            Mock(id="msg-2", role="user", content="Hi", timestamp="2025-07-02T10:01:00")
        ]
        mock_chat_engine_class.return_value = mock_service
        
        # API request
        response = test_client.get("/api/v1/chat/sessions/session-123/messages?skip=0&limit=10")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "assistant"
        assert data[1]["role"] == "user"
    
    def test_unauthorized_access(self, test_client):
        """Test API access without authentication."""
        # Override to remove authentication
        app.dependency_overrides[get_current_active_user] = lambda: None
        
        response = test_client.post(
            "/api/v1/chat/sessions",
            json={"strategy_id": "strategy-123", "patient_id": "patient-789"}
        )
        
        assert response.status_code == 401
```

#### 9.4 Integration Tests

Test end-to-end workflows with real database:

Create `app/tests/integration/test_chat_workflow.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from app.db.database import Base
from app.models.ai_chat import ChatSession, ChatMessage, DocumentChunk
from app.services.chat_engine import ChatEngineService
from app.repositories.chat_session_repository import ChatSessionRepository

@pytest.fixture(scope="module")
def postgres_container():
    """PostgreSQL container with pgvector extension."""
    with PostgresContainer(
        image="pgvector/pgvector:pg15",
        driver="psycopg2"
    ) as postgres:
        # Install pgvector extension
        connection = postgres.get_connection()
        cursor = connection.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        connection.commit()
        cursor.close()
        connection.close()
        
        yield postgres

@pytest.fixture
def test_engine(postgres_container):
    """Test database engine."""
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture
def test_db_session(test_engine):
    """Test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

class TestChatWorkflowIntegration:
    """Integration tests for complete chat workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_chat_session_workflow(self, test_db_session):
        """Test complete chat session from start to finish."""
        # Initialize service with real database
        chat_engine = ChatEngineService(test_db_session)
        
        # 1. Start chat session
        session = await chat_engine.start_chat_session(
            strategy_id="test-strategy-123",
            patient_id="test-patient-456",
            session_type="intake"
        )
        
        assert session.id is not None
        assert session.status == "active"
        
        # 2. Send first message
        response1 = await chat_engine.process_patient_response(
            session_id=session.id,
            user_message="I'm 45 years old and concerned about breast cancer risk"
        )
        
        assert response1.role == "assistant"
        assert len(response1.content) > 0
        
        # 3. Send follow-up message
        response2 = await chat_engine.process_patient_response(
            session_id=session.id,
            user_message="My mother and aunt both had breast cancer"
        )
        
        assert response2.role == "assistant"
        assert "family history" in response2.content.lower()
        
        # 4. Verify session data extraction
        updated_session = chat_engine.session_repo.get_session_by_id(session.id)
        assert "age" in updated_session.extracted_data
        assert "family_history" in updated_session.extracted_data
        
        # 5. Verify message history
        messages = chat_engine.message_repo.get_session_messages(session.id)
        assert len(messages) >= 4  # Welcome + 2 user + 2 assistant
    
    @pytest.mark.asyncio
    async def test_rag_knowledge_retrieval(self, test_db_session):
        """Test RAG knowledge retrieval with pgvector."""
        from app.services.rag_service import RAGService
        
        # Initialize RAG service
        rag_service = RAGService(test_db_session)
        
        # Create test document chunks
        chunk_repo = rag_service.chunk_repo
        
        # Mock embedding (in real scenario, this would come from OpenAI)
        test_embedding = [0.1] * 1536
        
        chunk_data = {
            "knowledge_source_id": "test-source-123",
            "content": "BRCA1 mutations significantly increase breast cancer risk",
            "embedding": test_embedding,
            "chunk_index": 0,
            "metadata": {"page": 1, "source": "brca_guidelines.pdf"}
        }
        
        # Create chunk
        chunk = chunk_repo.create_document_chunk(chunk_data)
        assert chunk.id is not None
        
        # Test similarity search
        results = chunk_repo.similarity_search(
            query_embedding=test_embedding,
            source_ids=["test-source-123"],
            limit=5
        )
        
        assert len(results) == 1
        assert results[0]["content"] == "BRCA1 mutations significantly increase breast cancer risk"
        assert results[0]["similarity_score"] > 0.99  # Should be very similar
        
        # Test keyword search
        keyword_results = chunk_repo.keyword_search(
            keywords=["BRCA1", "mutations"],
            source_ids=["test-source-123"],
            limit=5
        )
        
        assert len(keyword_results) == 1
        assert "BRCA1" in keyword_results[0]["content"]
```

#### 9.5 Performance Tests

Test system performance under load:

Create `app/tests/performance/test_chat_performance.py`:

```python
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from app.services.chat_engine import ChatEngineService
from app.services.rag_service import RAGService

class TestChatPerformance:
    """Performance tests for chat system."""
    
    @pytest.mark.asyncio
    async def test_concurrent_chat_sessions(self, test_db_session):
        """Test handling multiple concurrent chat sessions."""
        chat_engine = ChatEngineService(test_db_session)
        
        async def create_session(session_num):
            """Create a single chat session."""
            return await chat_engine.start_chat_session(
                strategy_id=f"strategy-{session_num}",
                patient_id=f"patient-{session_num}",
                session_type="intake"
            )
        
        # Create 10 concurrent sessions
        start_time = time.time()
        sessions = await asyncio.gather(*[
            create_session(i) for i in range(10)
        ])
        end_time = time.time()
        
        # Verify all sessions created successfully
        assert len(sessions) == 10
        assert all(session.id is not None for session in sessions)
        
        # Performance assertion (should complete in < 5 seconds)
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Concurrent session creation took {execution_time:.2f} seconds"
    
    @pytest.mark.asyncio
    async def test_rag_search_performance(self, test_db_session):
        """Test RAG search performance with large dataset."""
        rag_service = RAGService(test_db_session)
        
        # Create multiple test chunks
        chunk_repo = rag_service.chunk_repo
        test_embedding = [0.1] * 1536
        
        # Create 100 test chunks
        for i in range(100):
            chunk_data = {
                "knowledge_source_id": "perf-test-source",
                "content": f"Test content chunk {i} with various medical terms",
                "embedding": [0.1 + (i * 0.001)] * 1536,  # Slightly different embeddings
                "chunk_index": i,
                "metadata": {"chunk_id": i}
            }
            chunk_repo.create_document_chunk(chunk_data)
        
        # Test similarity search performance
        start_time = time.time()
        results = chunk_repo.similarity_search(
            query_embedding=test_embedding,
            source_ids=["perf-test-source"],
            limit=10
        )
        end_time = time.time()
        
        # Verify results
        assert len(results) == 10
        
        # Performance assertion (should complete in < 1 second)
        search_time = end_time - start_time
        assert search_time < 1.0, f"Similarity search took {search_time:.2f} seconds"
    
    @pytest.mark.asyncio
    async def test_message_processing_performance(self, test_db_session):
        """Test message processing performance."""
        chat_engine = ChatEngineService(test_db_session)
        
        # Create test session
        session = await chat_engine.start_chat_session(
            strategy_id="perf-test-strategy",
            patient_id="perf-test-patient",
            session_type="intake"
        )
        
        # Test processing 20 messages
        start_time = time.time()
        
        for i in range(20):
            await chat_engine.process_patient_response(
                session_id=session.id,
                user_message=f"Test message {i} with some medical context"
            )
        
        end_time = time.time()
        
        # Performance assertion (should complete in < 30 seconds)
        processing_time = end_time - start_time
        assert processing_time < 30.0, f"Message processing took {processing_time:.2f} seconds"
        
        # Verify all messages were processed
        messages = chat_engine.message_repo.get_session_messages(session.id)
        assert len(messages) >= 41  # 1 welcome + 20 user + 20 assistant
```

#### 9.6 Test Configuration

Create `pytest.ini` configuration:

```ini
[tool:pytest]
testpaths = app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --asyncio-mode=auto
markers =
    asyncio: marks tests as async
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    unit: marks tests as unit tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

Create `app/tests/conftest.py` for shared test fixtures:

```python
import pytest
import asyncio
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """Mock database session for unit tests."""
    return Mock()

@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return Mock(
        id="user-123",
        account_id="account-456",
        email="test@example.com",
        is_active=True
    )

@pytest.fixture
def sample_strategy():
    """Sample chat strategy for testing."""
    return Mock(
        id="strategy-123",
        name="Test Strategy",
        description="Test strategy for unit tests",
        specialty="General",
        account_id="account-456"
    )
```

#### 9.7 Running Tests

Execute tests with different scopes:

```bash
# Run all tests
pytest

# Run unit tests only
pytest app/tests/repositories/ app/tests/services/ -m "not integration"

# Run integration tests
pytest app/tests/integration/ -m integration

# Run performance tests
pytest app/tests/performance/ -m performance

# Run API tests
pytest app/tests/api/

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/services/test_chat_engine.py

# Run specific test method
pytest app/tests/services/test_chat_engine.py::TestChatEngineService::test_start_chat_session
```

#### 9.8 Test Data Management

Create test data factories for consistent testing:

```python
# app/tests/factories.py
import factory
from app.models.ai_chat import ChatSession, ChatMessage, DocumentChunk
from app.schemas.ai_chat import ChatSessionCreate, ChatMessageCreate

class ChatSessionFactory(factory.Factory):
    class Meta:
        model = ChatSession
    
    id = factory.Faker('uuid4')
    strategy_id = factory.Faker('uuid4')
    patient_id = factory.Faker('uuid4')
    session_type = "intake"
    status = "active"
    chat_context = factory.LazyFunction(lambda: {"specialty": "oncology"})
    extracted_data = factory.LazyFunction(lambda: {"age": 45})
    assessment_results = factory.LazyFunction(lambda: {})

class ChatMessageFactory(factory.Factory):
    class Meta:
        model = ChatMessage
    
    id = factory.Faker('uuid4')
    session_id = factory.Faker('uuid4')
    role = "user"
    content = factory.Faker('text', max_nb_chars=200)
    message_metadata = factory.LazyFunction(lambda: {})
    
class DocumentChunkFactory(factory.Factory):
    class Meta:
        model = DocumentChunk
    
    id = factory.Faker('uuid4')
    knowledge_source_id = factory.Faker('uuid4')
    content = factory.Faker('text', max_nb_chars=500)
    embedding = factory.LazyFunction(lambda: [0.1] * 1536)
    chunk_index = factory.Sequence(lambda n: n)
    metadata = factory.LazyFunction(lambda: {"page": 1})
```

This comprehensive testing implementation covers:

1. **Repository Layer**: Tests data access patterns and database operations
2. **Service Layer**: Tests business logic and service orchestration
3. **API Layer**: Tests HTTP endpoints and request/response handling
4. **Integration Tests**: Tests complete workflows with real database
5. **Performance Tests**: Tests system performance under load
6. **Test Configuration**: Proper pytest setup and fixtures

The tests follow the layered architecture pattern, ensuring each layer is tested independently while also validating the integration between layers.

Comprehensive testing strategy for the AI chat system following the layered architecture pattern. Tests are organized by layer: Repository → Service → API, with additional integration and end-to-end tests.

#### 9.1 Repository Layer Tests

Create test files for each repository to ensure proper database interactions:

**Test ChatSessionRepository** (`app/tests/repositories/test_chat_session_repository.py`):

```python
import pytest
from sqlalchemy.orm import Session
from app.repositories.chat_session_repository import ChatSessionRepository
from app.models.ai_chat import ChatSession, SessionStatus, SessionType
from app.schemas.ai_chat import ChatSessionCreate, ChatSessionUpdate
from app.tests.factories import ChatSessionFactory, AccountFactory

class TestChatSessionRepository:
    """Test chat session repository operations."""
    
    def setup_method(self):
        self.account = AccountFactory()
        self.repo = ChatSessionRepository(self.db)
    
    def test_create_session(self, db: Session):
        """Test creating a new chat session."""
        session_data = ChatSessionCreate(
            strategy_id="test-strategy-id",
            patient_id="test-patient-id",
            session_type=SessionType.SCREENING,
            status=SessionStatus.ACTIVE,
            chat_context={"initial": "context"},
            extracted_data={},
            assessment_results={}
        )
        
        session = self.repo.create_session(session_data)
        
        assert session.id is not None
        assert session.strategy_id == "test-strategy-id"
        assert session.patient_id == "test-patient-id"
        assert session.status == SessionStatus.ACTIVE
        assert session.chat_context == {"initial": "context"}
    
    def test_get_session_by_id(self, db: Session):
        """Test retrieving a session by ID."""
        created_session = ChatSessionFactory(account_id=self.account.id)
        db.add(created_session)
        db.commit()
        
        retrieved_session = self.repo.get_session_by_id(created_session.id)
        
        assert retrieved_session is not None
        assert retrieved_session.id == created_session.id
        assert retrieved_session.strategy_id == created_session.strategy_id
    
    def test_update_session(self, db: Session):
        """Test updating session data."""
        session = ChatSessionFactory(account_id=self.account.id)
        db.add(session)
        db.commit()
        
        updates = ChatSessionUpdate(
            status=SessionStatus.COMPLETED,
            extracted_data={"name": "John Doe", "age": 35}
        )
        
        updated_session = self.repo.update_session(session.id, updates)
        
        assert updated_session.status == SessionStatus.COMPLETED
        assert updated_session.extracted_data == {"name": "John Doe", "age": 35}
    
    def test_list_sessions_by_account(self, db: Session):
        """Test listing sessions with pagination."""
        # Create multiple sessions
        sessions = [
            ChatSessionFactory(account_id=self.account.id) for _ in range(3)
        ]
        db.add_all(sessions)
        db.commit()
        
        retrieved_sessions, total_count = self.repo.list_sessions_by_account(
            self.account.id, skip=0, limit=2
        )
        
        assert len(retrieved_sessions) == 2
        assert total_count == 3
```

**Test DocumentChunkRepository** (`app/tests/repositories/test_document_chunk_repository.py`):

```python
import pytest
from sqlalchemy.orm import Session
from app.repositories.chat_message_repository import DocumentChunkRepository
from app.models.ai_chat import DocumentChunk
from app.tests.factories import KnowledgeSourceFactory

class TestDocumentChunkRepository:
    """Test document chunk repository operations with pgvector."""
    
    def setup_method(self):
        self.knowledge_source = KnowledgeSourceFactory()
        self.repo = DocumentChunkRepository(self.db)
    
    def test_create_document_chunk(self, db: Session):
        """Test creating a document chunk with embedding."""
        chunk_data = {
            "knowledge_source_id": self.knowledge_source.id,
            "content": "This is a test document chunk about breast cancer screening.",
            "embedding": [0.1, 0.2, 0.3] * 512,  # 1536-dimensional embedding
            "chunk_index": 0,
            "metadata": {"source": "test_document.pdf", "page": 1}
        }
        
        chunk = self.repo.create_document_chunk(chunk_data)
        
        assert chunk.id is not None
        assert chunk.knowledge_source_id == self.knowledge_source.id
        assert chunk.content == chunk_data["content"]
        assert len(chunk.embedding) == 1536
        assert chunk.chunk_index == 0
        assert chunk.metadata == {"source": "test_document.pdf", "page": 1}
    
    def test_similarity_search(self, db: Session):
        """Test pgvector similarity search."""
        # Create test chunks with different embeddings
        chunk1_data = {
            "knowledge_source_id": self.knowledge_source.id,
            "content": "Breast cancer screening guidelines for women over 40.",
            "embedding": [0.9, 0.1, 0.0] * 512,
            "chunk_index": 0,
            "metadata": {"topic": "screening"}
        }
        
        chunk2_data = {
            "knowledge_source_id": self.knowledge_source.id,
            "content": "Genetic testing for BRCA1 and BRCA2 mutations.",
            "embedding": [0.1, 0.9, 0.0] * 512,
            "chunk_index": 1,
            "metadata": {"topic": "genetics"}
        }
        
        self.repo.create_document_chunk(chunk1_data)
        self.repo.create_document_chunk(chunk2_data)
        
        # Query embedding similar to chunk1
        query_embedding = [0.85, 0.15, 0.0] * 512
        
        results = self.repo.similarity_search(
            query_embedding=query_embedding,
            source_ids=[self.knowledge_source.id],
            limit=2,
            similarity_threshold=0.7
        )
        
        assert len(results) >= 1
        assert results[0]["content"] == chunk1_data["content"]
        assert results[0]["similarity_score"] > 0.7
    
    def test_keyword_search(self, db: Session):
        """Test full-text search using PostgreSQL."""
        chunk_data = {
            "knowledge_source_id": self.knowledge_source.id,
            "content": "Mammography screening recommendations for breast cancer detection.",
            "embedding": [0.1, 0.2, 0.3] * 512,
            "chunk_index": 0,
            "metadata": {"topic": "screening"}
        }
        
        self.repo.create_document_chunk(chunk_data)
        
        results = self.repo.keyword_search(
            keywords=["mammography", "screening"],
            source_ids=[self.knowledge_source.id],
            limit=5
        )
        
        assert len(results) == 1
        assert "mammography" in results[0]["content"].lower()
        assert results[0]["rank_score"] > 0
```

#### 9.2 Service Layer Tests

Test the business logic layer that orchestrates repository operations:

**Test ChatEngineService** (`app/tests/services/test_chat_engine.py`):

```python
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.chat_engine import ChatEngineService
from app.models.ai_chat import SessionType, SessionStatus, MessageRole
from app.schemas.ai_chat import ChatSessionCreate
from app.tests.factories import ChatStrategyFactory, PatientFactory

class TestChatEngineService:
    """Test chat engine service business logic."""
    
    def setup_method(self):
        self.service = ChatEngineService(self.db)
        self.strategy = ChatStrategyFactory()
        self.patient = PatientFactory()
    
    @patch('app.services.chat_engine.ChatEngineService._generate_welcome_message')
    def test_start_chat_session(self, mock_welcome, db: Session):
        """Test starting a new chat session."""
        mock_welcome.return_value = "Welcome to your screening session!"
        
        session = await self.service.start_chat_session(
            strategy_id=self.strategy.id,
            patient_id=self.patient.id,
            session_type=SessionType.SCREENING,
            initial_context={"patient_age": 35}
        )
        
        assert session.strategy_id == self.strategy.id
        assert session.patient_id == self.patient.id
        assert session.session_type == SessionType.SCREENING
        assert session.status == SessionStatus.ACTIVE
        assert session.chat_context == {"patient_age": 35}
        
        # Verify welcome message was created
        messages = self.service.message_repo.get_session_messages(session.id)
        assert len(messages) == 1
        assert messages[0].role == MessageRole.ASSISTANT
        assert messages[0].content == "Welcome to your screening session!"
    
    @patch('app.services.entity_extraction.EntityExtractionService.extract_entities')
    @patch('app.services.chat_engine.ChatEngineService._generate_ai_response')
    def test_process_patient_response(self, mock_ai_response, mock_extract, db: Session):
        """Test processing patient response with entity extraction."""
        # Setup mocks
        mock_extract.return_value = {"age": 35, "family_history": "mother"}
        mock_ai_response.return_value = {
            "content": "Thank you for sharing that information. Can you tell me more about your family history?",
            "metadata": {"next_question": "family_history_details"}
        }
        
        # Create session
        session = await self.service.start_chat_session(
            strategy_id=self.strategy.id,
            patient_id=self.patient.id,
            session_type=SessionType.SCREENING
        )
        
        # Process user response
        user_message = "I'm 35 years old and my mother had breast cancer."
        response = await self.service.process_patient_response(
            session_id=session.id,
            user_message=user_message,
            metadata={"timestamp": "2025-07-02T10:00:00Z"}
        )
        
        # Verify response
        assert response.role == MessageRole.ASSISTANT
        assert "family history" in response.content.lower()
        assert response.message_metadata["next_question"] == "family_history_details"
        
        # Verify session was updated with extracted data
        updated_session = self.service.session_repo.get_session_by_id(session.id)
        assert updated_session.extracted_data["age"] == 35
        assert updated_session.extracted_data["family_history"] == "mother"
    
    def test_validate_session_access(self, db: Session):
        """Test session access validation."""
        session = await self.service.start_chat_session(
            strategy_id=self.strategy.id,
            patient_id=self.patient.id,
            session_type=SessionType.SCREENING
        )
        
        # Test valid access
        validated_session = self.service.validate_session_access(session.id, self.patient.user)
        assert validated_session.id == session.id
        
        # Test invalid access
        other_user = Mock()
        other_user.id = "different-user-id"
        
        with pytest.raises(ValueError, match="Access denied"):
            self.service.validate_session_access(session.id, other_user)
```

**Test RAGService** (`app/tests/services/test_rag_service.py`):

```python
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.rag_service import RAGService
from app.tests.factories import KnowledgeSourceFactory

class TestRAGService:
    """Test RAG service with pgvector integration."""
    
    def setup_method(self):
        self.service = RAGService(self.db)
        self.knowledge_source = KnowledgeSourceFactory()
    
    @patch('app.services.rag_service.OpenAIEmbeddings')
    def test_index_knowledge_source(self, mock_embeddings, db: Session):
        """Test indexing a knowledge source into pgvector."""
        # Mock embedding generation
        mock_embeddings.return_value.embed_documents.return_value = [
            [0.1, 0.2, 0.3] * 512,  # First chunk embedding
            [0.4, 0.5, 0.6] * 512   # Second chunk embedding
        ]
        
        # Mock document content
        self.knowledge_source.content = "This is a test document. It contains medical information about breast cancer screening."
        
        await self.service.index_knowledge_source(self.knowledge_source)
        
        # Verify chunks were created
        chunks = self.service.chunk_repo.get_chunks_by_source(self.knowledge_source.id)
        assert len(chunks) >= 1
        assert all(len(chunk.embedding) == 1536 for chunk in chunks)
        assert all(chunk.content for chunk in chunks)
    
    @patch('app.services.rag_service.OpenAIEmbeddings')
    def test_retrieve_relevant_context(self, mock_embeddings, db: Session):
        """Test retrieving relevant context for a query."""
        # Setup mock embedding
        query_embedding = [0.1, 0.2, 0.3] * 512
        mock_embeddings.return_value.embed_query.return_value = query_embedding
        
        # Mock similarity search results
        mock_results = [
            {
                "content": "Breast cancer screening is recommended for women over 40.",
                "similarity_score": 0.85,
                "metadata": {"source": "guidelines.pdf", "page": 1}
            },
            {
                "content": "Genetic testing should be considered for high-risk patients.",
                "similarity_score": 0.78,
                "metadata": {"source": "genetics.pdf", "page": 3}
            }
        ]
        
        with patch.object(self.service.chunk_repo, 'similarity_search', return_value=mock_results):
            context = await self.service.retrieve_relevant_context(
                query="What are the screening guidelines for breast cancer?",
                source_ids=[self.knowledge_source.id],
                max_results=2
            )
        
        assert len(context) == 2
        assert context[0]["content"] == "Breast cancer screening is recommended for women over 40."
        assert context[0]["similarity_score"] == 0.85
        assert context[1]["similarity_score"] == 0.78
```

#### 9.3 API Layer Tests

Test the FastAPI endpoints and request/response handling:

**Test Chat Session API** (`app/tests/api/test_chat_sessions.py`):

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tests.factories import UserFactory, ChatStrategyFactory, PatientFactory
from app.api.auth import get_current_active_user

class TestChatSessionsAPI:
    """Test AI chat session API endpoints."""
    
    def setup_method(self):
        self.client = TestClient(app)
        self.user = UserFactory()
        self.strategy = ChatStrategyFactory(account_id=self.user.account_id)
        self.patient = PatientFactory()
        
        # Override auth dependency
        app.dependency_overrides[get_current_active_user] = lambda: self.user
    
    def test_start_chat_session(self):
        """Test starting a new chat session via API."""
        request_data = {
            "strategy_id": self.strategy.id,
            "patient_id": self.patient.id,
            "session_type": "screening",
            "initial_context": {"patient_age": 35}
        }
        
        response = self.client.post("/api/v1/chat/sessions", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == self.strategy.id
        assert data["patient_id"] == self.patient.id
        assert data["session_type"] == "screening"
        assert data["status"] == "active"
        assert data["chat_context"] == {"patient_age": 35}
    
    def test_send_message(self):
        """Test sending a message to a chat session."""
        # First create a session
        session_response = self.client.post("/api/v1/chat/sessions", json={
            "strategy_id": self.strategy.id,
            "patient_id": self.patient.id,
            "session_type": "screening"
        })
        session_id = session_response.json()["id"]
        
        # Send a message
        message_data = {
            "message": "I'm 35 years old and worried about breast cancer risk.",
            "message_metadata": {"timestamp": "2025-07-02T10:00:00Z"}
        }
        
        response = self.client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json=message_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "assistant"
        assert data["content"] is not None
        assert len(data["content"]) > 0
    
    def test_get_chat_session(self):
        """Test retrieving a chat session."""
        # Create session
        session_response = self.client.post("/api/v1/chat/sessions", json={
            "strategy_id": self.strategy.id,
            "patient_id": self.patient.id,
            "session_type": "screening"
        })
        session_id = session_response.json()["id"]
        
        # Get session
        response = self.client.get(f"/api/v1/chat/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["strategy_id"] == self.strategy.id
    
    def test_list_chat_sessions(self):
        """Test listing chat sessions with pagination."""
        # Create multiple sessions
        for i in range(3):
            self.client.post("/api/v1/chat/sessions", json={
                "strategy_id": self.strategy.id,
                "patient_id": self.patient.id,
                "session_type": "screening"
            })
        
        # List sessions
        response = self.client.get("/api/v1/chat/sessions?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 2
        assert data["total_count"] == 3
        assert data["skip"] == 0
        assert data["limit"] == 2
    
    def test_unauthorized_access(self):
        """Test unauthorized access to chat sessions."""
        # Remove auth override
        app.dependency_overrides.clear()
        
        response = self.client.post("/api/v1/chat/sessions", json={
            "strategy_id": self.strategy.id,
            "patient_id": self.patient.id,
            "session_type": "screening"
        })
        
        assert response.status_code == 401
```

#### 9.4 Integration Tests

Test the complete flow from API to database:

**Test Complete Chat Flow** (`app/tests/integration/test_chat_flow.py`):

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.tests.factories import UserFactory, ChatStrategyFactory, PatientFactory, KnowledgeSourceFactory
from app.api.auth import get_current_active_user

class TestChatFlowIntegration:
    """Test complete chat flow integration."""
    
    def setup_method(self):
        self.client = TestClient(app)
        self.user = UserFactory()
        self.strategy = ChatStrategyFactory(account_id=self.user.account_id)
        self.patient = PatientFactory()
        self.knowledge_source = KnowledgeSourceFactory()
        
        app.dependency_overrides[get_current_active_user] = lambda: self.user
    
    def test_complete_screening_conversation(self, db: Session):
        """Test a complete screening conversation flow."""
        # 1. Start chat session
        session_response = self.client.post("/api/v1/chat/sessions", json={
            "strategy_id": self.strategy.id,
            "patient_id": self.patient.id,
            "session_type": "screening",
            "initial_context": {"source": "patient_portal"}
        })
        
        assert session_response.status_code == 200
        session_id = session_response.json()["id"]
        
        # 2. Send patient responses
        conversation_flow = [
            {
                "message": "I'm 35 years old and my mother had breast cancer at 45.",
                "expected_extractions": ["age", "family_history"]
            },
            {
                "message": "I've never had genetic testing done.",
                "expected_extractions": ["genetic_testing_history"]
            },
            {
                "message": "I'm interested in learning about my risk level.",
                "expected_extractions": ["interest_in_assessment"]
            }
        ]
        
        for i, turn in enumerate(conversation_flow):
            # Send message
            message_response = self.client.post(
                f"/api/v1/chat/sessions/{session_id}/messages",
                json={"message": turn["message"]}
            )
            
            assert message_response.status_code == 200
            ai_response = message_response.json()
            assert ai_response["role"] == "assistant"
            assert len(ai_response["content"]) > 0
            
            # Verify session data extraction
            session_response = self.client.get(f"/api/v1/chat/sessions/{session_id}")
            session_data = session_response.json()
            
            # Check that extracted data is being populated
            assert "extracted_data" in session_data
            # Additional assertions based on extraction logic
        
        # 3. Verify complete session state
        final_session = self.client.get(f"/api/v1/chat/sessions/{session_id}")
        session_data = final_session.json()
        
        assert session_data["status"] in ["active", "completed"]
        assert len(session_data["extracted_data"]) > 0
        
        # 4. Verify message history
        messages_response = self.client.get(f"/api/v1/chat/sessions/{session_id}/messages")
        messages = messages_response.json()
        
        # Should have welcome message + user messages + AI responses
        expected_message_count = 1 + (len(conversation_flow) * 2)
        assert len(messages) == expected_message_count
        
        # Verify message order and roles
        assert messages[0]["role"] == "assistant"  # Welcome message
        for i in range(1, len(messages)):
            expected_role = "user" if i % 2 == 1 else "assistant"
            assert messages[i]["role"] == expected_role
```

#### 9.5 Performance Tests

Test system performance with realistic loads:

**Test RAG Performance** (`app/tests/performance/test_rag_performance.py`):

```python
import pytest
import time
from sqlalchemy.orm import Session
from app.services.rag_service import RAGService
from app.tests.factories import KnowledgeSourceFactory

class TestRAGPerformance:
    """Test RAG service performance with pgvector."""
    
    def setup_method(self):
        self.service = RAGService(self.db)
    
    def test_similarity_search_performance(self, db: Session):
        """Test similarity search performance with large dataset."""
        # Create knowledge source with many chunks
        knowledge_source = KnowledgeSourceFactory()
        
        # Create test chunks (simulate a large document)
        chunks_data = []
        for i in range(100):
            chunks_data.append({
                "knowledge_source_id": knowledge_source.id,
                "content": f"Test medical content chunk {i} about breast cancer screening.",
                "embedding": [0.1 * (i % 10), 0.2 * (i % 7), 0.3 * (i % 5)] * 512,
                "chunk_index": i,
                "metadata": {"chunk_id": i}
            })
        
        # Batch create chunks
        for chunk_data in chunks_data:
            self.service.chunk_repo.create_document_chunk(chunk_data)
        
        # Test search performance
        query_embedding = [0.1, 0.2, 0.3] * 512
        
        start_time = time.time()
        results = self.service.chunk_repo.similarity_search(
            query_embedding=query_embedding,
            source_ids=[knowledge_source.id],
            limit=10,
            similarity_threshold=0.5
        )
        end_time = time.time()
        
        # Performance assertions
        search_time = end_time - start_time
        assert search_time < 1.0  # Should complete within 1 second
        assert len(results) <= 10
        assert all(result["similarity_score"] >= 0.5 for result in results)
    
    def test_concurrent_searches(self, db: Session):
        """Test concurrent similarity searches."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        knowledge_source = KnowledgeSourceFactory()
        
        # Create test data
        for i in range(50):
            chunk_data = {
                "knowledge_source_id": knowledge_source.id,
                "content": f"Medical content about topic {i}",
                "embedding": [0.1 * i, 0.2 * i, 0.3 * i] * 512,
                "chunk_index": i,
                "metadata": {"topic": f"topic_{i}"}
            }
            self.service.chunk_repo.create_document_chunk(chunk_data)
        
        def perform_search(query_id):
            query_embedding = [0.1 * query_id, 0.2 * query_id, 0.3 * query_id] * 512
            return self.service.chunk_repo.similarity_search(
                query_embedding=query_embedding,
                source_ids=[knowledge_source.id],
                limit=5
            )
        
        # Run concurrent searches
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(perform_search, i) for i in range(10)]
            results = [future.result() for future in futures]
        end_time = time.time()
        
        # Verify all searches completed successfully
        assert len(results) == 10
        assert all(len(result) <= 5 for result in results)
        
        # Performance assertion
        total_time = end_time - start_time
        assert total_time < 5.0  # All searches should complete within 5 seconds
```

#### 9.6 Test Configuration

**Test Configuration** (`app/tests/conftest.py`):

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.core.config import settings

# Test database configuration
SQLALCHEMY_DATABASE_URL = "postgresql://test:test@localhost/test_genascope"

@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.rollback()
    session.close()

@pytest.fixture(autouse=True)
def clear_db(db):
    """Clear database between tests."""
    # Truncate all tables
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
```

#### 9.7 Running Tests

**Test Commands** (`run_tests.sh`):

```bash
#!/bin/bash

# Run all tests
pytest app/tests/ -v --tb=short

# Run tests by layer
pytest app/tests/repositories/ -v --tb=short  # Repository tests
pytest app/tests/services/ -v --tb=short     # Service tests  
pytest app/tests/api/ -v --tb=short          # API tests
pytest app/tests/integration/ -v --tb=short  # Integration tests

# Run performance tests
pytest app/tests/performance/ -v --tb=short --timeout=30

# Run with coverage
pytest app/tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest app/tests/services/test_chat_engine.py -v
```

This comprehensive testing strategy ensures:

1. **Repository Layer**: Database operations work correctly with pgvector
2. **Service Layer**: Business logic functions properly and calls repositories correctly
3. **API Layer**: HTTP endpoints handle requests/responses properly
4. **Integration**: Complete flows work end-to-end
5. **Performance**: System handles realistic loads efficiently
6. **Error Handling**: Edge cases and error conditions are properly handled

The tests follow the same layered architecture pattern as the implementation, making them maintainable and focused on their specific responsibilities.
