"""
Knowledge Source API Endpoints

FastAPI routes for uploading and managing knowledge sources
for AI chat strategies with vector search integration.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.auth import require_full_access, User
from app.services.rag_service import RAGService
from app.repositories.ai_chat_repository import AIChatRepository
from app.models.chat_configuration import KnowledgeSource

router = APIRouter(prefix="/knowledge", tags=["Knowledge Sources"])


@router.post("/upload", response_model=dict)
async def upload_knowledge_source(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    source_type: str = Form("document"),
    metadata: Optional[str] = Form(None),  # JSON string
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """Upload a knowledge source file for AI chat strategies.
    
    Supports various file formats (PDF, DOCX, TXT) and automatically
    processes them for vector search indexing.
    """
    try:
        import json
        import uuid
        from datetime import datetime
        
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.txt', '.doc'}
        file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in metadata field"
                )
        
        # Read file content
        file_content = await file.read()
        
        # Create knowledge source record
        ai_chat_repo = AIChatRepository(db)
        
        knowledge_source_data = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description or f"Uploaded file: {file.filename}",
            "source_type": source_type,
            "file_name": file.filename,
            "file_size": len(file_content),
            "file_path": f"uploads/{file.filename}",  # Would be actual storage path
            "processing_status": "uploaded",
            "metadata": {
                **parsed_metadata,
                "upload_user_id": current_user.id,
                "original_filename": file.filename,
                "file_size_bytes": len(file_content),
                "upload_timestamp": datetime.utcnow().isoformat()
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        knowledge_source = ai_chat_repo.create_knowledge_source(knowledge_source_data)
        
        # Process file in background
        rag_service = RAGService(db)
        background_tasks.add_task(
            rag_service.index_knowledge_source,
            knowledge_source
        )
        
        return {
            "id": knowledge_source.id,
            "name": knowledge_source.name,
            "status": "uploaded",
            "message": "File uploaded successfully. Processing in background.",
            "file_size": len(file_content),
            "processing_status": "uploaded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload knowledge source: {str(e)}"
        )


@router.get("/sources", response_model=List[dict])
async def get_knowledge_sources(
    source_type: Optional[str] = None,
    processing_status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """Get list of knowledge sources."""
    try:
        ai_chat_repo = AIChatRepository(db)
        
        # Get knowledge sources (would need to implement filtering in repository)
        sources = ai_chat_repo.get_knowledge_sources(
            source_type=source_type,
            processing_status=processing_status,
            limit=limit
        )
        
        # Convert to response format
        source_responses = []
        for source in sources:
            response_data = {
                "id": source.id,
                "name": source.name,
                "description": source.description,
                "source_type": source.source_type,
                "file_name": source.file_name,
                "file_size": source.file_size,
                "processing_status": source.processing_status,
                "created_at": source.created_at.isoformat() if source.created_at else None,
                "updated_at": source.updated_at.isoformat() if source.updated_at else None,
                "metadata": source.metadata
            }
            source_responses.append(response_data)
        
        return source_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge sources: {str(e)}"
        )


@router.get("/sources/{source_id}", response_model=dict)
async def get_knowledge_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """Get details of a specific knowledge source."""
    try:
        ai_chat_repo = AIChatRepository(db)
        
        source = ai_chat_repo.get_knowledge_source_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge source {source_id} not found"
            )
        
        # Get chunk count
        rag_service = RAGService(db)
        chunks = rag_service.get_knowledge_source_chunks(source_id)
        
        return {
            "id": source.id,
            "name": source.name,
            "description": source.description,
            "source_type": source.source_type,
            "file_name": source.file_name,
            "file_size": source.file_size,
            "processing_status": source.processing_status,
            "chunk_count": len(chunks),
            "created_at": source.created_at.isoformat() if source.created_at else None,
            "updated_at": source.updated_at.isoformat() if source.updated_at else None,
            "metadata": source.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge source: {str(e)}"
        )


@router.get("/sources/{source_id}/chunks", response_model=List[dict])
async def get_knowledge_source_chunks(
    source_id: str,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """Get document chunks for a knowledge source."""
    try:
        ai_chat_repo = AIChatRepository(db)
        
        # Validate source exists
        source = ai_chat_repo.get_knowledge_source_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge source {source_id} not found"
            )
        
        # Get chunks
        rag_service = RAGService(db)
        chunks = rag_service.get_knowledge_source_chunks(source_id, limit=limit)
        
        # Convert to response format
        chunk_responses = []
        for chunk in chunks:
            response_data = {
                "id": chunk.id,
                "knowledge_source_id": chunk.knowledge_source_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata,
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None
            }
            chunk_responses.append(response_data)
        
        return chunk_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge source chunks: {str(e)}"
        )


@router.post("/sources/{source_id}/reindex")
async def reindex_knowledge_source(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """Reindex a knowledge source (regenerate embeddings)."""
    try:
        ai_chat_repo = AIChatRepository(db)
        
        # Validate source exists
        source = ai_chat_repo.get_knowledge_source_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge source {source_id} not found"
            )
        
        # Reindex in background
        rag_service = RAGService(db)
        background_tasks.add_task(
            rag_service.reindex_knowledge_source,
            source_id
        )
        
        return {
            "id": source_id,
            "message": "Reindexing started in background",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex knowledge source: {str(e)}"
        )


@router.delete("/sources/{source_id}")
async def delete_knowledge_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """Delete a knowledge source and all its chunks."""
    try:
        ai_chat_repo = AIChatRepository(db)
        
        # Validate source exists
        source = ai_chat_repo.get_knowledge_source_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge source {source_id} not found"
            )
        
        # Delete chunks first
        ai_chat_repo.delete_chunks_by_knowledge_source(source_id)
        
        # Delete knowledge source
        ai_chat_repo.delete_knowledge_source(source_id)
        
        return {
            "id": source_id,
            "message": "Knowledge source deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge source: {str(e)}"
        )


@router.post("/search", response_model=List[dict])
async def search_knowledge(
    query: str,
    strategy_id: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """Search knowledge sources using vector similarity."""
    try:
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        rag_service = RAGService(db)
        
        results = await rag_service.search_knowledge(
            query=query,
            strategy_id=strategy_id,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge search failed: {str(e)}"
        )
