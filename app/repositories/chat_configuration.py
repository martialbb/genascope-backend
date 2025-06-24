"""
Repository layer for chat configuration models.

This module provides data access methods for chat strategies, knowledge sources,
targeting rules, and related entities.
"""
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, date
from app.repositories.base import BaseRepository
from app.models.chat_configuration import (
    ChatStrategy, KnowledgeSource, TargetingRule, OutcomeAction,
    StrategyExecution, StrategyAnalytics, StrategyKnowledgeSource
)
from app.schemas.chat_configuration import (
    ChatStrategyCreate, ChatStrategyUpdate,
    KnowledgeSourceCreate, KnowledgeSourceUpdate,
    KnowledgeSourceSearchRequest, ProcessingStatus
)


class ChatStrategyRepository(BaseRepository):
    """Repository for chat strategy operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, ChatStrategy)
    
    def get_by_account(self, account_id: str, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[ChatStrategy]:
        """Get all strategies for a specific account"""
        query = self.db.query(ChatStrategy).filter(ChatStrategy.account_id == account_id)
        
        if active_only:
            query = query.filter(ChatStrategy.is_active == True)
            
        return query.offset(skip).limit(limit).all()
    
    def get_by_account_with_details(self, account_id: str, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[ChatStrategy]:
        """Get all strategies for a specific account with full relationship details loaded"""
        query = (
            self.db.query(ChatStrategy)
            .options(
                selectinload(ChatStrategy.targeting_rules),
                selectinload(ChatStrategy.outcome_actions),
                selectinload(ChatStrategy.knowledge_sources)
            )
            .filter(ChatStrategy.account_id == account_id)
        )
        
        if active_only:
            query = query.filter(ChatStrategy.is_active == True)
            
        return query.offset(skip).limit(limit).all()
    
    def get_active_strategies(self, account_id: str) -> List[ChatStrategy]:
        """Get all active strategies for an account"""
        return (
            self.db.query(ChatStrategy)
            .filter(
                and_(
                    ChatStrategy.account_id == account_id,
                    ChatStrategy.is_active == True
                )
            )
            .all()
        )
    
    def get_with_full_details(self, strategy_id: str) -> Optional[ChatStrategy]:
        """Get strategy with all related data loaded"""
        return (
            self.db.query(ChatStrategy)
            .options(
                joinedload(ChatStrategy.knowledge_sources),
                joinedload(ChatStrategy.targeting_rules),
                joinedload(ChatStrategy.outcome_actions),
                joinedload(ChatStrategy.creator),
                joinedload(ChatStrategy.account)
            )
            .filter(ChatStrategy.id == strategy_id)
            .first()
        )
    
    def search_strategies(
        self, 
        account_id: str, 
        search_term: Optional[str] = None,
        specialty: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatStrategy]:
        """Search strategies with filters"""
        query = self.db.query(ChatStrategy).filter(ChatStrategy.account_id == account_id)
        
        if search_term:
            query = query.filter(
                or_(
                    ChatStrategy.name.ilike(f"%{search_term}%"),
                    ChatStrategy.description.ilike(f"%{search_term}%")
                )
            )
        
        if specialty:
            query = query.filter(ChatStrategy.specialty == specialty)
        
        if is_active is not None:
            query = query.filter(ChatStrategy.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def create_strategy(self, strategy_data: ChatStrategyCreate, user_id: str, account_id: str) -> ChatStrategy:
        """Create a new chat strategy"""
        strategy = ChatStrategy(
            name=strategy_data.name,
            description=strategy_data.description,
            goal=getattr(strategy_data, 'goal', strategy_data.description or ''),  # Use description as goal if not provided
            patient_introduction=strategy_data.patient_introduction,
            specialty=strategy_data.specialty,
            created_by=user_id,
            account_id=account_id
        )
        
        self.db.add(strategy)
        self.db.flush()  # Get the ID
        
        # Add targeting rules
        for rule_data in strategy_data.targeting_rules:
            rule = TargetingRule(
                strategy_id=strategy.id,
                field=rule_data.field,
                operator=rule_data.operator,
                value=rule_data.value,
                sequence=rule_data.sequence
            )
            self.db.add(rule)
        
        # Add outcome actions
        for action_data in strategy_data.outcome_actions:
            action = OutcomeAction(
                strategy_id=strategy.id,
                condition=action_data.condition,
                action_type=action_data.action_type,
                details=action_data.details,
                sequence=action_data.sequence
            )
            self.db.add(action)
        
        # Link knowledge sources
        for ks_id in strategy_data.knowledge_source_ids:
            link = StrategyKnowledgeSource(
                strategy_id=strategy.id,
                knowledge_source_id=ks_id
            )
            self.db.add(link)
        
        self.db.commit()
        return strategy
    
    def update_strategy(self, strategy_id: str, strategy_data: ChatStrategyUpdate) -> Optional[ChatStrategy]:
        """Update a chat strategy"""
        strategy = self.db.query(ChatStrategy).filter(ChatStrategy.id == strategy_id).first()
        if not strategy:
            return None
        
        # Update basic fields
        for field, value in strategy_data.dict(exclude_unset=True).items():
            setattr(strategy, field, value)
        
        strategy.updated_at = datetime.utcnow()
        self.db.commit()
        return strategy
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """Delete a chat strategy"""
        strategy = self.db.query(ChatStrategy).filter(ChatStrategy.id == strategy_id).first()
        if not strategy:
            return False
        
        self.db.delete(strategy)
        self.db.commit()
        return True


class KnowledgeSourceRepository(BaseRepository):
    """Repository for knowledge source operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, KnowledgeSource)
    
    def get_by_account(
        self, 
        account_id: str, 
        skip: int = 0, 
        limit: int = 100,
        source_type: Optional[str] = None,
        processing_status: Optional[str] = None,
        include_public: bool = True
    ) -> List[KnowledgeSource]:
        """Get knowledge sources for an account"""
        query = self.db.query(KnowledgeSource)
        
        # For now, just filter by account_id since is_public might not exist in DB
        query = query.filter(KnowledgeSource.account_id == account_id)
        
        if source_type:
            query = query.filter(KnowledgeSource.type == source_type)
            
        if processing_status:
            query = query.filter(KnowledgeSource.processing_status == processing_status)
        
        return query.filter(KnowledgeSource.is_active == True).offset(skip).limit(limit).all()
    
    def search_content(
        self, 
        request: KnowledgeSourceSearchRequest,
        account_id: str
    ) -> Dict[str, Any]:
        """Advanced search with full-text search and filters"""
        query = self.db.query(KnowledgeSource).filter(
            and_(
                or_(
                    KnowledgeSource.account_id == account_id,
                    KnowledgeSource.access_level == 'public'
                ),
                KnowledgeSource.is_active == True
            )
        )
        
        # Apply search query
        if request.query:
            query = query.filter(
                or_(
                    KnowledgeSource.name.ilike(f"%{request.query}%"),
                    KnowledgeSource.description.ilike(f"%{request.query}%"),
                    KnowledgeSource.content_summary.ilike(f"%{request.query}%")
                )
            )
        
        # Apply filters
        if request.category:
            # Note: category field doesn't exist in current model, skip for now
            pass
        
        if request.file_types:
            # Note: file_extension field doesn't exist in current model, skip for now  
            pass
        
        if request.processing_status:
            status_values = [status.value for status in request.processing_status]
            query = query.filter(KnowledgeSource.processing_status.in_(status_values))
        
        if request.specialty:
            # Note: specialty field doesn't exist in current model, skip for now
            pass
        
        if request.size_min:
            query = query.filter(KnowledgeSource.file_size >= request.size_min)
        
        if request.size_max:
            query = query.filter(KnowledgeSource.file_size <= request.size_max)
        
        if request.date_from:
            query = query.filter(KnowledgeSource.created_at >= request.date_from)
        
        if request.date_to:
            query = query.filter(KnowledgeSource.created_at <= request.date_to)
        
        # Apply sorting
        if request.sort_by == "date":
            order_col = KnowledgeSource.created_at
        elif request.sort_by == "size":
            order_col = KnowledgeSource.file_size
        elif request.sort_by == "title":
            order_col = KnowledgeSource.name
        elif request.sort_by == "last_accessed":
            order_col = KnowledgeSource.updated_at  # Use updated_at as proxy
        else:  # relevance - default to created_at for now
            order_col = KnowledgeSource.created_at
        
        if request.sort_order == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        items = query.offset(request.offset).limit(request.limit).all()
        
        # Generate facets
        facets = self._generate_facets(account_id)
        
        return {
            "items": items,
            "total": total,
            "has_more": total > (request.offset + request.limit),
            "facets": facets
        }
    
    def _generate_facets(self, account_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Generate facets for search filtering"""
        base_query = self.db.query(KnowledgeSource).filter(
            and_(
                KnowledgeSource.account_id == account_id,
                KnowledgeSource.is_active == True
            )
        )
        
        # Source type facets
        source_type_facets = (
            base_query
            .with_entities(KnowledgeSource.source_type, func.count(KnowledgeSource.id))
            .filter(KnowledgeSource.source_type.isnot(None))
            .group_by(KnowledgeSource.source_type)
            .all()
        )
        
        # Content type facets
        content_type_facets = (
            base_query
            .with_entities(KnowledgeSource.content_type, func.count(KnowledgeSource.id))
            .filter(KnowledgeSource.content_type.isnot(None))
            .group_by(KnowledgeSource.content_type)
            .all()
        )
        
        # Access level facets
        access_level_facets = (
            base_query
            .with_entities(KnowledgeSource.access_level, func.count(KnowledgeSource.id))
            .filter(KnowledgeSource.access_level.isnot(None))
            .group_by(KnowledgeSource.access_level)
            .all()
        )
        
        return {
            "source_types": [{"type": st, "count": count} for st, count in source_type_facets],
            "content_types": [{"type": ct, "count": count} for ct, count in content_type_facets],
            "access_levels": [{"level": al, "count": count} for al, count in access_level_facets]
        }
    
    def create_knowledge_source(self, ks_data: KnowledgeSourceCreate, user_id: str, account_id: str) -> KnowledgeSource:
        """Create a new knowledge source"""
        knowledge_source = KnowledgeSource(
            name=ks_data.name,
            source_type=ks_data.source_type,
            description=ks_data.description,
            content_type=ks_data.content_type,
            access_level=ks_data.access_level,
            created_by=user_id,
            account_id=account_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(knowledge_source)
        self.db.commit()
        self.db.refresh(knowledge_source)
        return knowledge_source
    
    def update_knowledge_source(self, ks_id: str, ks_data: KnowledgeSourceUpdate) -> Optional[KnowledgeSource]:
        """Update a knowledge source"""
        ks = self.db.query(KnowledgeSource).filter(KnowledgeSource.id == ks_id).first()
        if not ks:
            return None
        
        # Update fields with proper field mapping
        update_data = ks_data.model_dump(exclude_unset=True)
        
        # Map schema fields to model fields
        if 'title' in update_data:
            ks.name = update_data.pop('title')
        
        for field, value in update_data.items():
            if hasattr(ks, field):
                setattr(ks, field, value)
        
        ks.updated_at = datetime.utcnow()
        self.db.commit()
        return ks
    
    def update_processing_status(
        self, 
        ks_id: str, 
        status: ProcessingStatus,
        error: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Optional[KnowledgeSource]:
        """Update processing status and extracted content"""
        ks = self.db.query(KnowledgeSource).filter(KnowledgeSource.id == ks_id).first()
        if not ks:
            return None
        
        ks.processing_status = status.value
        ks.processing_error = error
        
        if status == ProcessingStatus.PROCESSING:
            ks.processing_attempts += 1
        elif status == ProcessingStatus.COMPLETED and extracted_data:
            ks.extracted_text = extracted_data.get('text')
            ks.content_summary = extracted_data.get('summary')
            ks.content_sections = extracted_data.get('sections')
            ks.keywords = extracted_data.get('keywords')
            ks.ai_insights = extracted_data.get('ai_insights')
            ks.content_extracted_at = datetime.utcnow()
        
        ks.updated_at = datetime.utcnow()
        self.db.commit()
        return ks
    
    def update_access_timestamp(self, ks_ids: List[str]) -> None:
        """Update last accessed timestamp for knowledge sources"""
        if not ks_ids:
            return
        
        self.db.query(KnowledgeSource).filter(
            KnowledgeSource.id.in_(ks_ids)
        ).update(
            {KnowledgeSource.last_accessed_at: datetime.utcnow()},
            synchronize_session=False
        )
        self.db.commit()
    
    def get_processing_queue(self, account_id: int) -> List[KnowledgeSource]:
        """Get knowledge sources waiting for processing for a specific account"""
        return (
            self.db.query(KnowledgeSource)
            .filter(
                KnowledgeSource.account_id == account_id,
                or_(
                    KnowledgeSource.processing_status == ProcessingStatus.PENDING.value,
                    KnowledgeSource.processing_status == ProcessingStatus.RETRY.value
                )
            )
            .order_by(KnowledgeSource.created_at)
            .all()
        )
    
    def bulk_update(self, ks_ids: List[str], updates: Dict[str, Any]) -> int:
        """Bulk update knowledge sources"""
        if not ks_ids:
            return 0
        
        updates['updated_at'] = datetime.utcnow()
        
        result = self.db.query(KnowledgeSource).filter(
            KnowledgeSource.id.in_(ks_ids)
        ).update(updates, synchronize_session=False)
        
        self.db.commit()
        return result
    
    def bulk_delete(self, ks_ids: List[str]) -> int:
        """Bulk delete knowledge sources"""
        if not ks_ids:
            return 0
        
        result = self.db.query(KnowledgeSource).filter(
            KnowledgeSource.id.in_(ks_ids)
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return result


class StrategyExecutionRepository(BaseRepository):
    """Repository for strategy execution operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, StrategyExecution)
    
    def get_by_strategy(self, strategy_id: str, skip: int = 0, limit: int = 100) -> List[StrategyExecution]:
        """Get executions for a specific strategy"""
        return (
            self.db.query(StrategyExecution)
            .filter(StrategyExecution.strategy_id == strategy_id)
            .order_by(desc(StrategyExecution.started_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_strategy_and_date_range(
        self, 
        strategy_id: str, 
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[StrategyExecution]:
        """Get executions for a specific strategy within a date range"""
        query = self.db.query(StrategyExecution).filter(StrategyExecution.strategy_id == strategy_id)
        
        if date_from:
            # Convert date to datetime for comparison with started_at
            from datetime import datetime, time
            datetime_from = datetime.combine(date_from, time.min)
            query = query.filter(StrategyExecution.started_at >= datetime_from)
        
        if date_to:
            # Convert date to datetime for comparison with started_at  
            from datetime import datetime, time
            datetime_to = datetime.combine(date_to, time.max)
            query = query.filter(StrategyExecution.started_at <= datetime_to)
        
        return query.order_by(desc(StrategyExecution.started_at)).all()
    
    def get_by_patient(self, patient_id: str, skip: int = 0, limit: int = 100) -> List[StrategyExecution]:
        """Get executions for a specific patient"""
        return (
            self.db.query(StrategyExecution)
            .filter(StrategyExecution.patient_id == patient_id)
            .order_by(desc(StrategyExecution.started_at))
            .offset(skip)
            .limit(limit)
            .all()
        )


class StrategyAnalyticsRepository(BaseRepository):
    """Repository for strategy analytics operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, StrategyAnalytics)
    
    def get_analytics_summary(
        self, 
        strategy_id: str, 
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get analytics summary for a strategy"""
        from datetime import datetime, time
        
        query = self.db.query(StrategyAnalytics).filter(StrategyAnalytics.strategy_id == strategy_id)
        
        if date_from:
            datetime_from = datetime.combine(date_from, time.min)
            query = query.filter(StrategyAnalytics.recorded_at >= datetime_from)
        if date_to:
            datetime_to = datetime.combine(date_to, time.max)
            query = query.filter(StrategyAnalytics.recorded_at <= datetime_to)
        
        analytics = query.all()
        
        if not analytics:
            return {
                "total_patients_screened": 0,
                "total_criteria_met": 0,
                "total_criteria_not_met": 0,
                "total_incomplete_data": 0,
                "conversion_rate": 0.0,
                "total_tasks_created": 0,
                "total_charts_flagged": 0,
                "total_messages_sent": 0,
                "total_followups_scheduled": 0
            }
        
        # Group analytics by metric name
        metrics = {}
        for a in analytics:
            if a.metric_name not in metrics:
                metrics[a.metric_name] = []
            metrics[a.metric_name].append(a.metric_value)
        
        # Calculate totals
        total_screened = sum(metrics.get("patients_screened", [0]))
        total_met = sum(metrics.get("criteria_met", [0]))
        total_not_met = sum(metrics.get("criteria_not_met", [0]))
        total_incomplete = sum(metrics.get("incomplete_data", [0]))
        
        return {
            "total_patients_screened": int(total_screened),
            "total_criteria_met": int(total_met),
            "total_criteria_not_met": int(total_not_met),
            "total_incomplete_data": int(total_incomplete),
            "conversion_rate": (total_met / total_screened * 100) if total_screened > 0 else 0.0,
            "total_tasks_created": int(sum(metrics.get("tasks_created", [0]))),
            "total_charts_flagged": int(sum(metrics.get("charts_flagged", [0]))),
            "total_messages_sent": int(sum(metrics.get("messages_sent", [0]))),
            "total_followups_scheduled": int(sum(metrics.get("followups_scheduled", [0]))),
            "date_range": {
                "from": min(a.recorded_at for a in analytics).date() if analytics else None,
                "to": max(a.recorded_at for a in analytics).date() if analytics else None
            }
        }
