"""
Service layer for chat configuration management.
Handles business logic for chat strategies, knowledge sources, file processing, and analytics.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, UploadFile

from app.repositories.chat_configuration import (
    ChatStrategyRepository,
    KnowledgeSourceRepository,
    StrategyExecutionRepository,
    StrategyAnalyticsRepository,
)
from app.services.storage import get_storage_client, StorageType, get_configured_storage_client
from app.services.content_processor import ContentProcessor
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
    StorageType as StorageTypeEnum,
    AccessLevel,
)
from app.models.chat_configuration import ChatStrategy, KnowledgeSource

logger = logging.getLogger(__name__)


class ChatStrategyService:
    """Service for managing chat strategies."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ChatStrategyRepository(db)
    
    def create_strategy(
        self,
        strategy_data: ChatStrategyCreate,
        creator_id: str,
        account_id: str
    ) -> ChatStrategyResponse:
        """Create a new chat strategy."""
        try:
            # Validate configuration if it exists
            if hasattr(strategy_data, 'configuration') and strategy_data.configuration:
                self._validate_strategy_config(strategy_data.configuration)
            
            strategy = self.repository.create_strategy(strategy_data, creator_id, account_id)
            
            # Manually construct response to avoid relationship issues
            return ChatStrategyResponse(
                id=str(strategy.id),
                name=strategy.name,
                description=strategy.description,
                goal=strategy.goal,
                patient_introduction=strategy.patient_introduction,
                specialty=strategy.specialty,
                is_active=strategy.is_active,
                created_by=str(strategy.created_by),
                account_id=str(strategy.account_id),
                version=strategy.version,
                created_at=strategy.created_at,
                updated_at=strategy.updated_at,
                knowledge_sources=[],
                targeting_rules=[],
                outcome_actions=[]
            )
        except IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="Strategy with this name already exists"
            )
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            raise HTTPException(status_code=500, detail="Failed to create strategy")
    
    def get_strategy(self, strategy_id: str, account_id: int) -> ChatStrategyResponse:
        """Get a strategy by ID."""
        strategy = self.repository.get_by_id(strategy_id)
        if not strategy or strategy.account_id != account_id:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Convert UUIDs to strings and create response manually to avoid DB errors
        return ChatStrategyResponse(
            id=str(strategy.id),
            name=strategy.name,
            description=strategy.description,
            patient_introduction=strategy.patient_introduction,
            specialty=strategy.specialty,
            goal=strategy.goal,  # Add the goal field
            is_active=strategy.is_active,
            version=strategy.version,
            created_by=str(strategy.created_by),
            account_id=str(strategy.account_id),
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
            knowledge_sources=[],  # Empty for now to avoid DB errors
            targeting_rules=[],     # Empty for now to avoid DB errors  
            outcome_actions=[]      # Empty for now to avoid DB errors
        )
    
    def list_strategies(
        self,
        account_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[ChatStrategyResponse]:
        """List strategies for an account."""
        strategies = self.repository.get_by_account(
            account_id, skip, limit, active_only
        )
        
        # Manually construct responses to avoid relationship issues
        result = []
        for strategy in strategies:
            response = ChatStrategyResponse(
                id=str(strategy.id),
                name=strategy.name,
                description=strategy.description,
                goal=strategy.goal,
                patient_introduction=strategy.patient_introduction,
                specialty=strategy.specialty,
                is_active=strategy.is_active,
                created_by=str(strategy.created_by),
                account_id=str(strategy.account_id),
                version=strategy.version,
                created_at=strategy.created_at,
                updated_at=strategy.updated_at,
                knowledge_sources=[],
                targeting_rules=[],
                outcome_actions=[]
            )
            result.append(response)
        
        return result
    
    def update_strategy(
        self,
        strategy_id: str,
        strategy_data: ChatStrategyUpdate,
        account_id: int
    ) -> ChatStrategyResponse:
        """Update a strategy."""
        strategy = self.repository.get_by_id(strategy_id)
        if not strategy or strategy.account_id != account_id:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if hasattr(strategy_data, 'configuration') and strategy_data.configuration:
            self._validate_strategy_config(strategy_data.configuration)
        
        updated_strategy = self.repository.update(strategy_id, strategy_data)
        
        # Manually construct response to avoid relationship issues
        return ChatStrategyResponse(
            id=str(updated_strategy.id),
            name=updated_strategy.name,
            description=updated_strategy.description,
            goal=updated_strategy.goal,
            patient_introduction=updated_strategy.patient_introduction,
            specialty=updated_strategy.specialty,
            is_active=updated_strategy.is_active,
            created_by=str(updated_strategy.created_by),
            account_id=str(updated_strategy.account_id),
            version=updated_strategy.version,
            created_at=updated_strategy.created_at,
            updated_at=updated_strategy.updated_at,
            knowledge_sources=[],
            targeting_rules=[],
            outcome_actions=[]
        )
    
    def delete_strategy(self, strategy_id: str, account_id: int) -> bool:
        """Delete a strategy."""
        from sqlalchemy import text
        import uuid
        
        # Validate UUID format first
        try:
            uuid_obj = uuid.UUID(strategy_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # First check if strategy exists and belongs to account using raw SQL
        result = self.db.execute(
            text("SELECT account_id FROM chat_strategies WHERE id = :strategy_id"),
            {"strategy_id": uuid_obj}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if str(result[0]) != str(account_id):
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Delete using raw SQL to avoid ORM relationship issues
        deleted_count = self.db.execute(
            text("DELETE FROM chat_strategies WHERE id = :strategy_id"),
            {"strategy_id": uuid_obj}
        ).rowcount
        
        self.db.commit()
        return deleted_count > 0
    
    def clone_strategy(
        self,
        strategy_id: str,
        new_name: str,
        account_id: int
    ) -> ChatStrategyResponse:
        """Clone an existing strategy."""
        original = self.repository.get_by_id(strategy_id)
        if not original or original.account_id != account_id:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        clone_data = ChatStrategyCreate(
            name=new_name,
            description=f"Clone of {original.description}",
            goal=original.goal,
            patient_introduction=original.patient_introduction,
            specialty=original.specialty
        )
        
        return self.create_strategy(clone_data, original.created_by, account_id)
    
    def _validate_strategy_config(self, config: Dict[str, Any]) -> None:
        """Validate strategy configuration."""
        if not config:
            return
            
        required_fields = ["chat_type", "questions"]
        for field in required_fields:
            if field not in config:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required configuration field: {field}"
                )
        
        if not isinstance(config.get("questions"), list):
            raise HTTPException(
                status_code=400,
                detail="Questions must be a list"
            )


class KnowledgeSourceService:
    """Service for managing knowledge sources and file uploads."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeSourceRepository(db)
        # For now, we'll skip storage client and content processor setup
        # since they require async operations
    
    def create_knowledge_source(
        self,
        source_data: KnowledgeSourceCreate,
        account_id: str,
        user_id: str
    ) -> KnowledgeSourceResponse:
        """Create a new knowledge source."""
        try:
            # Prepare data with required fields
            create_data = source_data.model_dump()
            create_data.update({
                "account_id": account_id,
                "created_by": user_id,  # Use the actual user ID
                "processing_status": "pending",
                "is_active": True
            })
            
            source = self.repository.create(create_data)
            
            # Manually construct response to match KnowledgeSourceResponse schema
            return KnowledgeSourceResponse(
                id=str(source.id),
                name=source.name,  # Keep original name field
                source_type=source.source_type,  # Keep original source_type field
                description=source.description or "",
                content_type=source.content_type,
                access_level=source.access_level,
                created_at=source.created_at,
                updated_at=source.updated_at,
                account_id=str(source.account_id),  # Required field
                file_name=None,
                file_extension=None,
                file_size_bytes=getattr(source, 'file_size', None),
                file_checksum=None,
                storage_type=StorageTypeEnum.LOCAL,  # Default storage type
                storage_provider=None,
                processing_status=ProcessingStatus.PENDING,
                processing_error=None,
                processing_attempts=0,
                content_extracted_at=None,
                content_summary=getattr(source, 'content_summary', None),
                keywords=[],
                ai_insights=None,
                upload_date=source.created_at,
                uploaded_by=str(source.created_by),
                is_active=source.is_active,
                is_public=False,  # Default since we removed this from model
                last_accessed_at=None,
                archived_at=None
            )
        except IntegrityError as ie:
            logger.error(f"IntegrityError creating knowledge source: {ie}")
            raise HTTPException(
                status_code=400,
                detail="Knowledge source with this name already exists"
            )
        except Exception as e:
            logger.error(f"Error creating knowledge source: {e}")
            raise HTTPException(status_code=500, detail="Failed to create knowledge source")
    
    async def upload_file(
        self,
        file: UploadFile,
        request: FileUploadRequest,
        account_id: str,
        user_id: str
    ) -> KnowledgeSourceResponse:
        """Upload and process a file as a knowledge source."""
        try:
            # Get configured storage client
            storage_client = get_configured_storage_client()
            
            # Import settings for bucket configuration
            from app.core.config import settings
            
            # Generate unique key for the file while preserving original filename
            import uuid
            from pathlib import Path
            import re
            
            # Clean and sanitize the original filename
            original_filename = file.filename or "unknown_file"
            # Remove any path separators and invalid characters
            clean_filename = re.sub(r'[^\w\-_\.]', '_', original_filename)
            clean_filename = clean_filename.replace('/', '_').replace('\\', '_')
            
            # Generate unique identifier to avoid conflicts
            file_id = str(uuid.uuid4())[:8]  # Use first 8 characters for shorter names
            
            # Construct storage key: account_id/filename_with_uuid.ext
            file_stem = Path(clean_filename).stem
            file_extension = Path(clean_filename).suffix
            
            # Format: account_id/originalname_uuid.ext
            storage_key = f"{account_id}/{file_stem}_{file_id}{file_extension}"
            
            # Upload file to storage
            upload_result = await storage_client.upload_file(
                file=file.file,
                bucket=settings.STORAGE_BUCKET,
                key=storage_key,
                content_type=file.content_type or "application/octet-stream",
                metadata={
                    "original_filename": str(file.filename) if file.filename else "",
                    "account_id": str(account_id),
                    "user_id": str(user_id),
                    "upload_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Create the database record with storage information
            create_data = {
                "name": request.title,  # Map title to name for database
                "source_type": "file",
                "description": request.description or "",
                "content_type": file.content_type,
                "file_path": storage_key,  # Store the storage key (preserves original filename structure)
                "file_size": upload_result.size,
                "s3_bucket": upload_result.bucket,
                "s3_key": upload_result.key,
                "s3_url": upload_result.url,
                "access_level": request.access_level.value if hasattr(request.access_level, 'value') else str(request.access_level),
                "processing_status": "pending",
                "is_active": True,
                "account_id": account_id,
                "created_by": user_id
            }
            
            source = self.repository.create(create_data)
            
            # Manually construct response to match KnowledgeSourceResponse schema
            return KnowledgeSourceResponse(
                id=str(source.id),
                name=source.name,
                source_type=source.source_type,
                description=source.description or "",
                content_type=source.content_type,
                access_level=source.access_level,
                created_at=source.created_at,
                updated_at=source.updated_at,
                account_id=str(source.account_id),
                file_name=file.filename,  # Original filename as uploaded
                file_extension=file_extension.lstrip('.') if file_extension else None,
                file_size_bytes=source.file_size,
                file_checksum=upload_result.checksum,
                storage_type=StorageTypeEnum.LOCAL,  # Will be dynamic based on config
                storage_provider=settings.STORAGE_PROVIDER,
                processing_status=ProcessingStatus.PENDING,
                processing_error=None,
                processing_attempts=0,
                content_extracted_at=None,
                content_summary=getattr(source, 'content_summary', None),
                keywords=[],
                ai_insights=None,
                upload_date=source.created_at,
                uploaded_by=str(source.created_by),
                is_active=source.is_active,
                is_public=False,
                last_accessed_at=None,
                archived_at=None
            )
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    def direct_upload(
        self,
        request: DirectUploadRequest,
        creator_id: int
    ) -> KnowledgeSourceResponse:
        """Create knowledge source from direct content."""
        try:
            source_data = KnowledgeSourceCreate(
                name=request.name,
                description=request.description,
                source_type="direct",
                storage_type=StorageTypeEnum.database,
                content=request.content,
                access_level=request.access_level or AccessLevel.private,
                processing_status=ProcessingStatus.completed,
                metadata_={
                    "content_type": request.content_type,
                    "tags": request.tags or [],
                    "created_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            source = self.repository.create(source_data, creator_id)
            return KnowledgeSourceResponse.from_orm(source)
            
        except Exception as e:
            logger.error(f"Error creating direct upload: {e}")
            raise HTTPException(status_code=500, detail="Failed to create direct upload")
    
    def get_knowledge_source(
        self,
        source_id: str,
        account_id: str
    ) -> KnowledgeSourceResponse:
        """Get a knowledge source by ID."""
        from sqlalchemy import text
        import uuid
        
        # Validate UUID format first
        try:
            uuid_obj = uuid.UUID(source_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        # Use raw SQL to get the knowledge source
        result = self.db.execute(
            text("""
            SELECT id, name, source_type, description, created_at, updated_at,
                   content_type, file_size, file_path, s3_bucket, s3_key, s3_url,
                   processing_status, is_active, access_level, created_by, account_id
            FROM knowledge_sources 
            WHERE id = :source_id AND account_id = :account_id
            """),
            {"source_id": uuid_obj, "account_id": account_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        # Manually construct response
        return KnowledgeSourceResponse(
            id=str(result.id),
            name=result.name,
            source_type=result.source_type,
            description=result.description or "",
            content_type=result.content_type,
            access_level=result.access_level,
            created_at=result.created_at,
            updated_at=result.updated_at,
            account_id=str(result.account_id),
            file_name=None,  # Could be extracted from file_path if needed
            file_extension=None,  # Could be extracted from file_path if needed
            file_size_bytes=result.file_size,
            file_checksum=None,  # Not stored in current schema
            storage_type=StorageTypeEnum.LOCAL,
            storage_provider="local",
            processing_status=ProcessingStatus.PENDING,
            processing_error=None,
            processing_attempts=0,
            content_extracted_at=None,
            content_summary=None,
            keywords=[],
            ai_insights=None,
            upload_date=result.created_at,
            uploaded_by=str(result.created_by),
            is_active=result.is_active,
            is_public=False,
            last_accessed_at=None,
            archived_at=None
        )
    
    def list_knowledge_sources(
        self,
        account_id: int,
        skip: int = 0,
        limit: int = 100,
        source_type: Optional[str] = None,
        processing_status: Optional[ProcessingStatus] = None
    ) -> List[KnowledgeSourceResponse]:
        """List knowledge sources for an account."""
        # Use raw SQL to avoid ORM schema mismatch issues
        from sqlalchemy import text
        
        query = """
        SELECT id, name, source_type, description, created_at, updated_at,
               content_type, file_size, file_path, s3_bucket, s3_key, s3_url,
               processing_status, is_active, access_level, created_by, account_id
        FROM knowledge_sources 
        WHERE account_id = :account_id
        """
        
        params = {"account_id": account_id}
        
        if source_type:
            query += " AND source_type = :source_type"
            params["source_type"] = source_type
            
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
        
        result = self.db.execute(text(query), params).fetchall()
        
        # Manually construct responses to match KnowledgeSourceResponse schema
        sources = []
        for row in result:
            response = KnowledgeSourceResponse(
                id=str(row.id),
                name=row.name,  # Keep original name field
                source_type=row.source_type,  # Keep original source_type field
                description=row.description or "",
                content_type=row.content_type,
                access_level=row.access_level,
                created_at=row.created_at,
                updated_at=row.updated_at,
                account_id=str(row.account_id),  # Required field
                file_name=None,
                file_extension=None,
                file_size_bytes=row.file_size,
                file_checksum=None,
                storage_type=StorageTypeEnum.LOCAL,  # Default storage type
                storage_provider=None,
                processing_status=ProcessingStatus.COMPLETED if row.processing_status == "completed" else ProcessingStatus.PENDING,
                processing_error=None,
                processing_attempts=0,
                content_extracted_at=None,
                content_summary=None,
                keywords=[],
                ai_insights=None,
                upload_date=row.created_at,
                uploaded_by=str(row.created_by),
                is_active=row.is_active,
                is_public=False,  # Default since we removed this from model
                last_accessed_at=None,
                archived_at=None
            )
            sources.append(response)
            
        return sources
    
    def search_knowledge_sources(
        self,
        search_params: KnowledgeSourceSearchRequest,
        account_id: int
    ) -> List[KnowledgeSourceResponse]:
        """Search knowledge sources."""
        sources = self.repository.search(search_params, account_id)
        return [KnowledgeSourceResponse.from_orm(s) for s in sources]
    
    def update_knowledge_source(
        self,
        source_id: int,
        update_data: KnowledgeSourceUpdate,
        account_id: int
    ) -> KnowledgeSourceResponse:
        """Update a knowledge source."""
        source = self.repository.get_by_id(source_id)
        if not source or source.account_id != account_id:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        updated_source = self.repository.update(source_id, update_data)
        return KnowledgeSourceResponse.from_orm(updated_source)
    
    async def delete_knowledge_source(
        self,
        source_id: str,
        account_id: str
    ) -> bool:
        """Delete a knowledge source and its associated file."""
        from sqlalchemy import text
        import uuid
        
        # Validate UUID format first
        try:
            uuid_obj = uuid.UUID(source_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        # First get the source details including file path using raw SQL
        result = self.db.execute(
            text("""
            SELECT account_id, file_path, s3_bucket, s3_key 
            FROM knowledge_sources 
            WHERE id = :source_id
            """),
            {"source_id": uuid_obj}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        if str(result[0]) != str(account_id):
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        # Delete the file from storage if it exists
        if result.s3_bucket and result.s3_key:
            try:
                storage_client = get_configured_storage_client()
                await storage_client.delete_file(result.s3_bucket, result.s3_key)
            except Exception as e:
                logger.warning(f"Failed to delete file from storage: {e}")
                # Continue with database deletion even if file deletion fails
        
        # Delete from database using raw SQL to avoid ORM relationship issues
        deleted_count = self.db.execute(
            text("DELETE FROM knowledge_sources WHERE id = :source_id"),
            {"source_id": uuid_obj}
        ).rowcount
        
        self.db.commit()
        return deleted_count > 0
    
    def bulk_delete_knowledge_sources(
        self,
        source_ids: List[int],
        account_id: int
    ) -> int:
        """Bulk delete knowledge sources."""
        # Verify all sources belong to the account
        for source_id in source_ids:
            source = self.repository.get_by_id(source_id)
            if not source or source.account_id != account_id:
                raise HTTPException(
                    status_code=404,
                    detail=f"Knowledge source {source_id} not found"
                )
        
        return self.repository.bulk_delete(source_ids)
    
    def get_processing_queue(self, account_id: int) -> List[KnowledgeSourceResponse]:
        """Get knowledge sources in processing queue."""
        sources = self.repository.get_processing_queue(account_id)
        return [KnowledgeSourceResponse.from_orm(s) for s in sources]
    
    def retry_processing(self, source_id: int, account_id: int) -> bool:
        """Retry processing for a failed knowledge source."""
        source = self.repository.get_by_id(source_id)
        if not source or source.account_id != account_id:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        if source.processing_status != ProcessingStatus.failed:
            raise HTTPException(
                status_code=400,
                detail="Only failed sources can be retried"
            )
        
        # Reset status to pending
        self.repository.update(source_id, KnowledgeSourceUpdate(
            processing_status=ProcessingStatus.pending
        ))
        
        return True


class StrategyAnalyticsService:
    """Service for strategy analytics and reporting."""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics_repository = StrategyAnalyticsRepository(db)
        self.execution_repository = StrategyExecutionRepository(db)
    
    def get_strategy_analytics(
        self,
        strategy_id: str,
        account_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a strategy."""
        # Verify strategy belongs to account
        strategy_repo = ChatStrategyRepository(self.db)
        strategy = strategy_repo.get_by_id(strategy_id)
        if not strategy or strategy.account_id != account_id:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics data
        analytics = self.analytics_repository.get_by_strategy_and_date_range(
            strategy_id, start_date, end_date
        )
        
        # Get execution summary
        executions = self.execution_repository.get_by_strategy_and_date_range(
            strategy_id, start_date, end_date
        )
        
        # Calculate metrics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == "completed"])
        avg_duration = sum([e.duration_seconds or 0 for e in executions]) / max(total_executions, 1)
        
        outcomes = {}
        for execution in executions:
            if execution.outcome:
                outcomes[execution.outcome] = outcomes.get(execution.outcome, 0) + 1
        
        return {
            "strategy_id": strategy_id,
            "period": f"{days} days",
            "summary": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": successful_executions / max(total_executions, 1),
                "average_duration_seconds": avg_duration,
                "outcomes": outcomes
            },
            "analytics": [
                {
                    "date": a.date.isoformat(),
                    "metrics": a.metrics
                }
                for a in analytics
            ],
            "executions": [
                {
                    "id": e.id,
                    "patient_id": e.patient_id,
                    "status": e.status,
                    "outcome": e.outcome,
                    "duration_seconds": e.duration_seconds,
                    "created_at": e.created_at.isoformat()
                }
                for e in executions
            ]
        }
    
    def get_account_analytics(
        self,
        account_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for all strategies in an account."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all strategies for account
        strategy_repo = ChatStrategyRepository(self.db)
        strategies = strategy_repo.get_by_account(account_id)
        
        account_analytics = {
            "account_id": account_id,
            "period": f"{days} days",
            "total_strategies": len(strategies),
            "active_strategies": len([s for s in strategies if s.is_active]),
            "strategy_analytics": []
        }
        
        # Get analytics for each strategy
        for strategy in strategies:
            strategy_analytics = self.get_strategy_analytics(
                strategy.id, account_id, days
            )
            account_analytics["strategy_analytics"].append({
                "strategy_name": strategy.name,
                **strategy_analytics["summary"]
            })
        
        return account_analytics
