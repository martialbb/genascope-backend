"""
API endpoints for chat configuration management.
Handles REST API for chat strategies, knowledge sources, file uploads, and analytics.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.services.chat_configuration_sync import (
    ChatStrategyService,
    KnowledgeSourceService,
    StrategyAnalyticsService,
)
from app.schemas.chat_configuration import (
    ChatStrategyCreate,
    ChatStrategyUpdate,
    ChatStrategyResponse,
    KnowledgeSourceCreate,
    KnowledgeSourceUpdate,
    KnowledgeSourceResponse,
    KnowledgeSourceSearchRequest,
    FileUploadRequest,
    DirectUploadRequest,
    ProcessingStatus,
    AccessLevel,
)

router = APIRouter(prefix="/api/v1/chat-configuration", tags=["Chat Configuration"])
security = HTTPBearer()


# Chat Strategy Endpoints
@router.post("/strategies", response_model=ChatStrategyResponse)
def create_chat_strategy(
    strategy_data: ChatStrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new chat strategy."""
    # For now, use user's account_id if available, otherwise raise error
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = ChatStrategyService(db)
    return service.create_strategy(strategy_data, current_user.id, account_id)


@router.get("/strategies", response_model=List[ChatStrategyResponse])
def list_chat_strategies(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List chat strategies for the current account."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = ChatStrategyService(db)
    return service.list_strategies(account_id, skip, limit, active_only)


@router.get("/strategies/{strategy_id}", response_model=ChatStrategyResponse)
def get_chat_strategy(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific chat strategy."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = ChatStrategyService(db)
    return service.get_strategy(strategy_id, account_id)


@router.put("/strategies/{strategy_id}", response_model=ChatStrategyResponse)
def update_chat_strategy(
    strategy_id: str,
    strategy_data: ChatStrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a chat strategy."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = ChatStrategyService(db)
    return service.update_strategy(strategy_id, strategy_data, account_id)


@router.delete("/strategies/{strategy_id}")
def delete_chat_strategy(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a chat strategy."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = ChatStrategyService(db)
    success = service.delete_strategy(strategy_id, account_id)
    if success:
        return {"message": "Strategy deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete strategy")


@router.post("/strategies/{strategy_id}/clone", response_model=ChatStrategyResponse)
def clone_chat_strategy(
    strategy_id: str,
    new_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Clone an existing chat strategy."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = ChatStrategyService(db)
    return service.clone_strategy(strategy_id, new_name, account_id)


# Knowledge Source Endpoints
@router.post("/knowledge-sources", response_model=KnowledgeSourceResponse)
def create_knowledge_source(
    source_data: KnowledgeSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new knowledge source."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    user_id = getattr(current_user, 'id', None)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")
    
    service = KnowledgeSourceService(db)
    return service.create_knowledge_source(source_data, account_id, user_id)


@router.post("/knowledge-sources/upload", response_model=KnowledgeSourceResponse)
async def upload_file_knowledge_source(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,  # JSON string of tags
    access_level: Optional[str] = "private",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file as a knowledge source."""
    import json
    
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    user_id = getattr(current_user, 'id', None)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")
    
    # Parse tags if provided
    parsed_tags = []
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except json.JSONDecodeError:
            parsed_tags = [tags]  # Single tag as string
    
    request = FileUploadRequest(
        title=name or file.filename,  # Use title instead of name
        description=description or "",
        tags=parsed_tags,
        access_level=AccessLevel.ACCOUNT if access_level == "account" else AccessLevel.USER
    )
    
    service = KnowledgeSourceService(db)
    return await service.upload_file(file, request, account_id, user_id)


@router.post("/knowledge-sources/direct", response_model=KnowledgeSourceResponse)
def create_direct_knowledge_source(
    request: DirectUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a knowledge source from direct content."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    return service.direct_upload(request, account_id)


@router.get("/knowledge-sources", response_model=List[KnowledgeSourceResponse])
def list_knowledge_sources(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[str] = None,
    processing_status: Optional[ProcessingStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List knowledge sources for the current account."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    return service.list_knowledge_sources(
        account_id, skip, limit, source_type, processing_status
    )


@router.get("/knowledge-sources/{source_id}", response_model=KnowledgeSourceResponse)
def get_knowledge_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific knowledge source."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    return service.get_knowledge_source(source_id, account_id)


@router.put("/knowledge-sources/{source_id}", response_model=KnowledgeSourceResponse)
def update_knowledge_source(
    source_id: str,
    update_data: KnowledgeSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a knowledge source."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    return service.update_knowledge_source(source_id, update_data, account_id)


@router.delete("/knowledge-sources/{source_id}")
async def delete_knowledge_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a knowledge source."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    success = await service.delete_knowledge_source(source_id, account_id)
    if success:
        return {"message": "Knowledge source deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete knowledge source")


@router.post("/knowledge-sources/search", response_model=List[KnowledgeSourceResponse])
def search_knowledge_sources(
    search_params: KnowledgeSourceSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search knowledge sources."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    return service.search_knowledge_sources(search_params, account_id)


@router.delete("/knowledge-sources/bulk")
def bulk_delete_knowledge_sources(
    source_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk delete knowledge sources."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    deleted_count = service.bulk_delete_knowledge_sources(source_ids, account_id)
    return {"message": f"Successfully deleted {deleted_count} knowledge sources"}


@router.get("/knowledge-sources/processing/queue", response_model=List[KnowledgeSourceResponse])
def get_processing_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get knowledge sources in processing queue."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    return service.get_processing_queue(account_id)


@router.post("/knowledge-sources/{source_id}/retry")
def retry_processing(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retry processing for a failed knowledge source."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = KnowledgeSourceService(db)
    success = service.retry_processing(source_id, account_id)
    if success:
        return {"message": "Processing retry initiated"}
    raise HTTPException(status_code=500, detail="Failed to retry processing")


# Analytics Endpoints
@router.get("/strategies/{strategy_id}/analytics")
def get_strategy_analytics(
    strategy_id: str,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get analytics for a specific strategy."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = StrategyAnalyticsService(db)
    return service.get_strategy_analytics(strategy_id, account_id, days)


@router.get("/analytics/account")
def get_account_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get analytics for all strategies in the account."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
    
    service = StrategyAnalyticsService(db)
    return service.get_account_analytics(account_id, days)


# Health and Status Endpoints
@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat-configuration"}


@router.get("/stats")
def get_configuration_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get basic statistics for chat configuration."""
    account_id = getattr(current_user, 'account_id', None)
    if not account_id:
        raise HTTPException(status_code=400, detail="User must be associated with an account")
        
    strategy_service = ChatStrategyService(db)
    knowledge_service = KnowledgeSourceService(db)
    
    strategies = strategy_service.list_strategies(account_id)
    knowledge_sources = knowledge_service.list_knowledge_sources(account_id)
    
    processing_queue = knowledge_service.get_processing_queue(account_id)
    
    return {
        "total_strategies": len(strategies),
        "active_strategies": len([s for s in strategies if s.is_active]),
        "total_knowledge_sources": len(knowledge_sources),
        "processing_queue_length": len(processing_queue),
        "knowledge_source_types": {
            "file": len([ks for ks in knowledge_sources if ks.source_type == "file"]),
            "direct": len([ks for ks in knowledge_sources if ks.source_type == "direct"]),
            "url": len([ks for ks in knowledge_sources if ks.source_type == "url"])
        }
    }
