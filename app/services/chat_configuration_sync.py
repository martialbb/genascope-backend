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
    ExecutionStatus,
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
            
            # Reload the strategy with full details to get the relationships
            strategy_with_details = self.repository.get_with_full_details(str(strategy.id))
            if not strategy_with_details:
                raise HTTPException(status_code=500, detail="Failed to retrieve created strategy")
            
            # Load targeting rules from database (sorted by sequence)
            targeting_rules = []
            for rule in sorted(strategy_with_details.targeting_rules, key=lambda r: r.sequence):
                targeting_rules.append({
                    "id": str(rule.id),
                    "strategy_id": str(rule.strategy_id),
                    "field": rule.field,
                    "operator": rule.operator,
                    "value": rule.value,
                    "sequence": rule.sequence,
                    "created_at": rule.created_at
                })
            
            # Load outcome actions from database (sorted by sequence)
            outcome_actions = []
            for action in sorted(strategy_with_details.outcome_actions, key=lambda a: a.sequence):
                outcome_actions.append({
                    "id": str(action.id),
                    "strategy_id": str(action.strategy_id),
                    "condition": action.condition,
                    "action_type": action.action_type,
                    "details": action.details,
                    "sequence": action.sequence,
                    "created_at": action.created_at
                })
            
            # Load knowledge sources from database
            knowledge_sources = []
            for ks_assoc in strategy_with_details.knowledge_sources:
                # Access the actual knowledge source through the association
                ks = ks_assoc.knowledge_source
                # Create a comprehensive knowledge source response
                ks_response = {
                    "id": str(ks.id),
                    "name": ks.name,
                    "source_type": ks.source_type,
                    "description": ks.description or "",
                    "content_type": ks.content_type,
                    "access_level": ks.access_level or "account",
                    "file_name": getattr(ks, 'file_path', None),
                    "file_extension": None,
                    "file_size_bytes": getattr(ks, 'file_size', None),
                    "file_checksum": None,
                    "storage_type": "database",
                    "storage_provider": None,
                    "processing_status": ks.processing_status or "completed",
                    "processing_error": getattr(ks, 'processing_error', None),
                    "processing_attempts": 0,
                    "content_extracted_at": getattr(ks, 'processed_at', None),
                    "content_summary": getattr(ks, 'content_summary', None),
                    "keywords": [],
                    "ai_insights": None,
                    "upload_date": ks.created_at,
                    "uploaded_by": str(ks.created_by),
                    "account_id": str(ks.account_id),
                    "is_active": getattr(ks, 'is_active', True),
                    "is_public": False,
                    "last_accessed_at": None,
                    "archived_at": None,
                    "created_at": ks.created_at,
                    "updated_at": ks.updated_at
                }
                knowledge_sources.append(ks_response)
            
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
                knowledge_sources=knowledge_sources,
                targeting_rules=targeting_rules,
                outcome_actions=outcome_actions
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
        strategy = self.repository.get_with_full_details(strategy_id)
        if not strategy or strategy.account_id != account_id:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Load targeting rules from database
        targeting_rules = []
        for rule in sorted(strategy.targeting_rules, key=lambda r: r.sequence):
            targeting_rules.append({
                "id": str(rule.id),
                "strategy_id": str(rule.strategy_id),
                "field": rule.field,
                "operator": rule.operator,
                "value": rule.value,
                "sequence": rule.sequence,
                "created_at": rule.created_at
            })
        
        # Load outcome actions from database
        outcome_actions = []
        for action in sorted(strategy.outcome_actions, key=lambda a: a.sequence):
            outcome_actions.append({
                "id": str(action.id),
                "strategy_id": str(action.strategy_id),
                "condition": action.condition,
                "action_type": action.action_type,
                "details": action.details,
                "sequence": action.sequence,
                "created_at": action.created_at
            })
        
        # Load knowledge sources from database
        knowledge_sources = []
        for ks_assoc in strategy.knowledge_sources:
            # Access the actual knowledge source through the association
            ks = ks_assoc.knowledge_source
            # Create a comprehensive knowledge source response
            ks_response = {
                "id": str(ks.id),
                "name": ks.name,
                "source_type": ks.source_type,
                "description": ks.description or "",
                "content_type": ks.content_type,
                "access_level": ks.access_level or "account",
                "file_name": getattr(ks, 'file_path', None),
                "file_extension": None,
                "file_size_bytes": getattr(ks, 'file_size', None),
                "file_checksum": None,
                "storage_type": "database",
                "storage_provider": None,
                "processing_status": ks.processing_status or "completed",
                "processing_error": getattr(ks, 'processing_error', None),
                "processing_attempts": 0,
                "content_extracted_at": getattr(ks, 'processed_at', None),
                "content_summary": getattr(ks, 'content_summary', None),
                "keywords": [],
                "ai_insights": None,
                "upload_date": ks.created_at,
                "uploaded_by": str(ks.created_by),
                "account_id": str(ks.account_id),
                "is_active": getattr(ks, 'is_active', True),
                "is_public": False,
                "last_accessed_at": None,
                "archived_at": None,
                "created_at": ks.created_at,
                "updated_at": ks.updated_at
            }
            knowledge_sources.append(ks_response)
        
        return ChatStrategyResponse(
            id=str(strategy.id),
            name=strategy.name,
            description=strategy.description,
            patient_introduction=strategy.patient_introduction,
            specialty=strategy.specialty,
            goal=strategy.goal,
            is_active=strategy.is_active,
            version=strategy.version,
            created_by=str(strategy.created_by),
            account_id=str(strategy.account_id),
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
            knowledge_sources=knowledge_sources,
            targeting_rules=targeting_rules,
            outcome_actions=outcome_actions
        )
    
    def list_strategies(
        self,
        account_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        specialty: Optional[str] = None
    ) -> List[ChatStrategyResponse]:
        """List strategies for an account."""
        strategies = self.repository.get_by_account_with_details(
            account_id, skip, limit, active_only, specialty
        )
        
        # Construct responses with full relationship data
        result = []
        for strategy in strategies:
            # Load targeting rules from database (sorted by sequence)
            targeting_rules = []
            for rule in sorted(strategy.targeting_rules, key=lambda r: r.sequence):
                targeting_rules.append({
                    "id": str(rule.id),
                    "strategy_id": str(rule.strategy_id),
                    "field": rule.field,
                    "operator": rule.operator,
                    "value": rule.value,
                    "sequence": rule.sequence,
                    "created_at": rule.created_at
                })
            
            # Load outcome actions from database (sorted by sequence)
            outcome_actions = []
            for action in sorted(strategy.outcome_actions, key=lambda a: a.sequence):
                outcome_actions.append({
                    "id": str(action.id),
                    "strategy_id": str(action.strategy_id),
                    "condition": action.condition,
                    "action_type": action.action_type,
                    "details": action.details,
                    "sequence": action.sequence,
                    "created_at": action.created_at
                })
            
            # Load knowledge sources from database
            knowledge_sources = []
            for ks_assoc in strategy.knowledge_sources:
                # Access the actual knowledge source through the association
                ks = ks_assoc.knowledge_source
                # Create a comprehensive knowledge source response
                ks_response = {
                    "id": str(ks.id),
                    "name": ks.name,
                    "source_type": ks.source_type,
                    "description": ks.description or "",
                    "content_type": ks.content_type,
                    "access_level": ks.access_level or "account",
                    "file_name": getattr(ks, 'file_path', None),
                    "file_extension": None,
                    "file_size_bytes": getattr(ks, 'file_size', None),
                    "file_checksum": None,
                    "storage_type": "database",
                    "storage_provider": None,
                    "processing_status": ks.processing_status or "completed",
                    "processing_error": getattr(ks, 'processing_error', None),
                    "processing_attempts": 0,
                    "content_extracted_at": getattr(ks, 'processed_at', None),
                    "content_summary": getattr(ks, 'content_summary', None),
                    "keywords": [],
                    "ai_insights": None,
                    "upload_date": ks.created_at,
                    "uploaded_by": str(ks.created_by),
                    "account_id": str(ks.account_id),
                    "is_active": getattr(ks, 'is_active', True),
                    "is_public": False,
                    "last_accessed_at": None,
                    "archived_at": None,
                    "created_at": ks.created_at,
                    "updated_at": ks.updated_at
                }
                knowledge_sources.append(ks_response)
            
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
                knowledge_sources=knowledge_sources,
                targeting_rules=targeting_rules,
                outcome_actions=outcome_actions
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
            uuid.UUID(strategy_id)  # Just validate, don't convert
        except ValueError:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # First check if strategy exists and belongs to account using raw SQL
        result = self.db.execute(
            text("SELECT account_id FROM chat_strategies WHERE id = :strategy_id"),
            {"strategy_id": strategy_id}  # Use string directly
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        if str(result[0]) != str(account_id):
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Delete using raw SQL to avoid ORM relationship issues
        deleted_count = self.db.execute(
            text("DELETE FROM chat_strategies WHERE id = :strategy_id"),
            {"strategy_id": strategy_id}  # Use string directly
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
        creator_id: str,
        account_id: str
    ) -> KnowledgeSourceResponse:
        """Create knowledge source from direct content."""
        try:
            source_data = KnowledgeSourceCreate(
                name=request.name,
                description=request.description,
                source_type="direct",
                content_type=request.content_type
            )
            
            source = self.repository.create_knowledge_source(source_data, creator_id, account_id)
            return self._convert_to_response(source)
            
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
        
        source = self.repository.get_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        # Check account access
        if str(source.account_id) != str(account_id):
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        return self._convert_to_response(source)
    
    def list_knowledge_sources(
        self,
        account_id: str,
        skip: int = 0,
        limit: int = 100,
        source_type: Optional[str] = None,
        processing_status: Optional[ProcessingStatus] = None
    ) -> List[KnowledgeSourceResponse]:
        """List knowledge sources for an account."""
        # Use the repository to get knowledge sources
        sources = self.repository.get_by_account(
            account_id=account_id,
            skip=skip,
            limit=limit,
            source_type=source_type,
            include_public=True
        )
        
        return [self._convert_to_response(source) for source in sources]
    
    def search_knowledge_sources(
        self,
        search_params: KnowledgeSourceSearchRequest,
        account_id: str
    ) -> List[KnowledgeSourceResponse]:
        """Search knowledge sources."""
        result = self.repository.search_content(search_params, account_id)
        sources = result.get("items", []) if isinstance(result, dict) else result
        return [self._convert_to_response(source) for source in sources]
    
    def update_knowledge_source(
        self,
        source_id: str,
        update_data: KnowledgeSourceUpdate,
        account_id: str
    ) -> KnowledgeSourceResponse:
        """Update a knowledge source."""
        source = self.repository.get_by_id(source_id)
        if not source or str(source.account_id) != str(account_id):
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        updated_source = self.repository.update_knowledge_source(source_id, update_data)
        return self._convert_to_response(updated_source)
    
    def _convert_to_response(self, source) -> KnowledgeSourceResponse:
        """Convert database model to response schema with proper field mapping."""
        return KnowledgeSourceResponse(
            id=str(source.id),
            name=source.name,
            source_type=source.source_type,
            description=source.description or "",
            content_type=source.content_type,
            access_level=source.access_level,
            file_name=None,  # Not in current model
            file_extension=None,  # Not in current model
            file_size_bytes=source.file_size,
            file_checksum=None,  # Not in current model
            storage_type="local",  # Default value since not in model
            storage_provider=None,  # Not in current model
            processing_status=source.processing_status or "pending",
            processing_error=source.processing_error,
            processing_attempts=0,  # Not in current model
            content_extracted_at=source.processed_at,
            content_summary=source.content_summary,
            keywords=[],  # Not in current model
            ai_insights=None,  # Not in current model
            upload_date=source.created_at,
            uploaded_by=str(source.created_by),
            account_id=str(source.account_id),
            is_active=source.is_active,
            is_public=False,  # Not in current model
            last_accessed_at=None,  # Not in current model
            archived_at=None,  # Not in current model
            created_at=source.created_at,
            updated_at=source.updated_at
        )
    
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
            uuid.UUID(source_id)  # Just validate, don't convert
        except ValueError:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        # First get the source details including file path using raw SQL
        result = self.db.execute(
            text("""
            SELECT account_id, file_path 
            FROM knowledge_sources 
            WHERE id = :source_id
            """),
            {"source_id": source_id}  # Use string directly
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        if str(result[0]) != str(account_id):
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        # Note: S3 file deletion is not implemented yet since s3_bucket/s3_key columns don't exist
        # TODO: Add S3 storage columns and implement file cleanup when storage integration is added
        
        # Delete from database using raw SQL to avoid ORM relationship issues
        deleted_count = self.db.execute(
            text("DELETE FROM knowledge_sources WHERE id = :source_id"),
            {"source_id": source_id}  # Use string directly
        ).rowcount
        
        self.db.commit()
        return deleted_count > 0
    
    def bulk_delete_knowledge_sources(
        self,
        source_ids: List[str],
        account_id: str
    ) -> int:
        """Bulk delete knowledge sources."""
        # Verify all sources belong to the account
        for i, source_id in enumerate(source_ids):
            source = self.repository.get_by_id(source_id)
            if not source:
                raise HTTPException(
                    status_code=404,
                    detail=f"Knowledge source not found: {source_id} (position {i})"
                )
            if str(source.account_id) != str(account_id):
                raise HTTPException(
                    status_code=404,
                    detail=f"Knowledge source access denied: {source_id} (account mismatch: {source.account_id} != {account_id})"
                )
        
        return self.repository.bulk_delete(source_ids)
    
    def get_processing_queue(self, account_id: int) -> List[KnowledgeSourceResponse]:
        """Get knowledge sources in processing queue."""
        sources = self.repository.get_processing_queue(account_id)
        return [self._convert_to_response(s) for s in sources]
    
    def retry_processing(self, source_id: str, account_id: str) -> bool:
        """Retry processing for a failed knowledge source."""
        source = self.repository.get_by_id(source_id)
        if not source or str(source.account_id) != str(account_id):
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        
        if source.processing_status != ProcessingStatus.FAILED.value:
            raise HTTPException(
                status_code=400,
                detail="Only failed sources can be retried"
            )
        
        # Reset status to pending by directly updating the database object
        source.processing_status = ProcessingStatus.PENDING.value
        self.db.commit()
        self.db.refresh(source)
        
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
        account_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a strategy."""
        # Verify strategy belongs to account
        strategy_repo = ChatStrategyRepository(self.db)
        strategy = strategy_repo.get_by_id(strategy_id)
        if not strategy or str(strategy.account_id) != str(account_id):
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Calculate date range for analytics
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query analytics metrics from the database
        analytics_query = text("""
            SELECT 
                SUM(patients_screened) as total_patients_screened,
                SUM(criteria_met) as total_criteria_met,
                SUM(criteria_not_met) as total_criteria_not_met,
                SUM(incomplete_data) as total_incomplete_data,
                SUM(tasks_created) as total_tasks_created,
                SUM(charts_flagged) as total_charts_flagged,
                SUM(messages_sent) as total_messages_sent,
                SUM(followups_scheduled) as total_followups_scheduled,
                AVG(avg_duration_minutes) as avg_duration_minutes
            FROM strategy_analytics 
            WHERE strategy_id = :strategy_id 
                AND date >= :start_date 
                AND date <= :end_date
        """)
        
        analytics_result = self.db.execute(analytics_query, {
            "strategy_id": strategy_id,
            "start_date": start_date.date(),
            "end_date": end_date.date()
        }).fetchone()
        
        # Extract metrics from the result row
        if analytics_result:
            (total_patients_screened, total_criteria_met, total_criteria_not_met, 
             total_incomplete_data, total_tasks_created, total_charts_flagged,
             total_messages_sent, total_followups_scheduled, avg_duration_minutes) = analytics_result
            
            # Convert None values to 0
            total_patients_screened = total_patients_screened or 0
            total_criteria_met = total_criteria_met or 0
            total_criteria_not_met = total_criteria_not_met or 0
            total_incomplete_data = total_incomplete_data or 0
            total_tasks_created = total_tasks_created or 0
            total_charts_flagged = total_charts_flagged or 0
            total_messages_sent = total_messages_sent or 0
            total_followups_scheduled = total_followups_scheduled or 0
            avg_duration_minutes = avg_duration_minutes or 0
        else:
            # No analytics data found
            (total_patients_screened, total_criteria_met, total_criteria_not_met, 
             total_incomplete_data, total_tasks_created, total_charts_flagged,
             total_messages_sent, total_followups_scheduled, avg_duration_minutes) = (0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # Query execution data
        executions_query = text("""
            SELECT execution_status, started_at, completed_at, executed_actions
            FROM strategy_executions 
            WHERE strategy_id = :strategy_id 
                AND started_at >= :start_date 
                AND started_at <= :end_date
            ORDER BY started_at DESC
        """)
        
        executions_result = self.db.execute(executions_query, {
            "strategy_id": strategy_id,
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        # Calculate execution summary
        total_executions = len(executions_result)
        successful_executions = len([e for e in executions_result if e[0] == 'completed'])
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
        
        # Calculate average duration for completed executions
        total_duration = 0
        completed_count = 0
        for execution in executions_result:
            if execution[0] == 'completed' and execution[1] and execution[2]:
                duration = (execution[2] - execution[1]).total_seconds()
                total_duration += duration
                completed_count += 1
        
        average_duration = total_duration / completed_count if completed_count > 0 else 0.0
        
        # Prepare execution details
        executions = []
        for execution in executions_result[:10]:  # Limit to 10 most recent
            executions.append({
                "status": execution[0],
                "started_at": execution[1].isoformat() if execution[1] else None,
                "completed_at": execution[2].isoformat() if execution[2] else None,
                "results": execution[3] if execution[3] else {}
            })
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "period": f"{days} days",
            "summary": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": round(success_rate, 2),
                "average_duration_seconds": round(average_duration, 2),
                "outcomes": {}
            },
            "analytics": {
                "patients_screened": int(total_patients_screened),
                "criteria_met": int(total_criteria_met),
                "criteria_not_met": int(total_criteria_not_met),
                "incomplete_data": int(total_incomplete_data),
                "conversion_rate": round((total_criteria_met / total_patients_screened * 100) if total_patients_screened > 0 else 0.0, 2),
                "total_tasks_created": int(total_tasks_created),
                "total_charts_flagged": int(total_charts_flagged),
                "total_messages_sent": int(total_messages_sent),
                "total_followups_scheduled": int(total_followups_scheduled)
            },
            "executions": executions
        }
        
    def get_account_analytics(
        self,
        account_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for all strategies in an account."""
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        # Get all strategies for account
        strategy_repo = ChatStrategyRepository(self.db)
        strategies = strategy_repo.get_by_account(account_id)
        
        # Calculate date range for analytics
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        strategy_analytics = []
        for strategy in strategies:
            # Query analytics metrics for this strategy  
            analytics_query = text("""
                SELECT 
                    SUM(patients_screened) as total_patients_screened,
                    SUM(criteria_met) as total_criteria_met,
                    SUM(criteria_not_met) as total_criteria_not_met,
                    SUM(incomplete_data) as total_incomplete_data,
                    SUM(tasks_created) as total_tasks_created,
                    SUM(charts_flagged) as total_charts_flagged,
                    SUM(messages_sent) as total_messages_sent,
                    SUM(followups_scheduled) as total_followups_scheduled
                FROM strategy_analytics 
                WHERE strategy_id = :strategy_id 
                    AND date >= :start_date 
                    AND date <= :end_date
            """)
            
            analytics_result = self.db.execute(analytics_query, {
                "strategy_id": str(strategy.id),
                "start_date": start_date.date(),
                "end_date": end_date.date()
            }).fetchone()
            
            # Extract metrics from the result row
            if analytics_result:
                (total_patients_screened, total_criteria_met, total_criteria_not_met, 
                 total_incomplete_data, total_tasks_created, total_charts_flagged,
                 total_messages_sent, total_followups_scheduled) = analytics_result
                
                # Convert None values to 0
                total_patients_screened = total_patients_screened or 0
                total_criteria_met = total_criteria_met or 0
                total_criteria_not_met = total_criteria_not_met or 0
                total_incomplete_data = total_incomplete_data or 0
                total_tasks_created = total_tasks_created or 0
                total_charts_flagged = total_charts_flagged or 0
                total_messages_sent = total_messages_sent or 0
                total_followups_scheduled = total_followups_scheduled or 0
            else:
                # No analytics data found
                (total_patients_screened, total_criteria_met, total_criteria_not_met, 
                 total_incomplete_data, total_tasks_created, total_charts_flagged,
                 total_messages_sent, total_followups_scheduled) = (0, 0, 0, 0, 0, 0, 0, 0)
            
            # Query execution data for this strategy
            executions_query = text("""
                SELECT execution_status, started_at, completed_at
                FROM strategy_executions 
                WHERE strategy_id = :strategy_id 
                    AND started_at >= :start_date 
                    AND started_at <= :end_date
            """)
            
            executions_result = self.db.execute(executions_query, {
                "strategy_id": str(strategy.id),
                "start_date": start_date,
                "end_date": end_date
            }).fetchall()
            
            # Calculate execution summary
            total_executions = len(executions_result)
            successful_executions = len([e for e in executions_result if e[0] == 'completed'])
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
            
            strategy_analytics.append({
                "strategy_id": str(strategy.id),
                "strategy_name": strategy.name,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": round(success_rate, 2),
                "analytics": {
                    "patients_screened": int(total_patients_screened),
                    "criteria_met": int(total_criteria_met),
                    "criteria_not_met": int(total_criteria_not_met),
                    "incomplete_data": int(total_incomplete_data),
                    "conversion_rate": round((total_criteria_met / total_patients_screened * 100) if total_patients_screened > 0 else 0.0, 2),
                    "total_tasks_created": int(total_tasks_created),
                    "total_charts_flagged": int(total_charts_flagged),
                    "total_messages_sent": int(total_messages_sent),
                    "total_followups_scheduled": int(total_followups_scheduled)
                }
            })
        
        return {
            "account_id": account_id,
            "period": f"{days} days",
            "total_strategies": len(strategies),
            "active_strategies": len([s for s in strategies if s.is_active]),
            "strategy_analytics": strategy_analytics
        }
