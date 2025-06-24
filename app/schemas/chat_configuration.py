"""
Pydantic schema models for chat configuration related data transfer objects.

These schemas define the structure for request and response payloads
related to chat strategy configuration, knowledge sources, and targeting rules.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime, date


class StrategySpecialty(str, Enum):
    """Enumeration of medical specialties"""
    ONCOLOGY = "Oncology"
    CARDIOLOGY = "Cardiology"
    GASTROENTEROLOGY = "Gastroenterology"
    HEPATOLOGY = "Hepatology"
    PHARMACY = "Pharmacy"
    GENETICS = "Genetics"
    OTHER = "Other"


class KnowledgeSourceType(str, Enum):
    """Enumeration of knowledge source types"""
    GUIDELINE = "guideline"
    RESEARCH_PAPER = "research_paper"
    PROTOCOL = "protocol"
    RISK_MODEL = "risk_model"
    CUSTOM_DOCUMENT = "custom_document"
    CUSTOM_LINK = "custom_link"


class ProcessingStatus(str, Enum):
    """Enumeration of processing statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class StorageType(str, Enum):
    """Enumeration of storage types"""
    S3 = "s3"
    MINIO = "minio"
    DATABASE = "database"  # Legacy
    LOCAL = "local"  # Development


class AccessLevel(str, Enum):
    """Enumeration of access levels"""
    ACCOUNT = "account"
    USER = "user"
    PUBLIC = "public"


class TargetingOperator(str, Enum):
    """Enumeration of targeting rule operators"""
    IS = "is"
    IS_NOT = "is_not"
    IS_BETWEEN = "is_between"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class OutcomeCondition(str, Enum):
    """Enumeration of outcome conditions"""
    MEETS_CRITERIA = "meets_criteria"
    DOES_NOT_MEET_CRITERIA = "does_not_meet_criteria"
    INCOMPLETE_DATA = "incomplete_data"


class OutcomeActionType(str, Enum):
    """Enumeration of outcome action types"""
    CREATE_TASK = "create_task"
    FLAG_CHART = "flag_chart"
    SEND_MESSAGE = "send_message"
    SCHEDULE_FOLLOWUP = "schedule_followup"


class ExecutionStatus(str, Enum):
    """Enumeration of strategy execution statuses"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Base schemas for common fields
class BaseTimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Knowledge Source schemas
class KnowledgeSourceBase(BaseModel):
    """Base schema for knowledge sources"""
    name: str = Field(..., min_length=1, max_length=255)
    source_type: str
    description: str
    content_type: Optional[str] = None
    access_level: str = "account"


class KnowledgeSourceCreate(KnowledgeSourceBase):
    """Schema for creating knowledge sources"""
    pass


class KnowledgeSourceUpdate(BaseModel):
    """Schema for updating knowledge sources"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    specialty: Optional[str] = None
    version: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    access_level: Optional[AccessLevel] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    processing_status: Optional[ProcessingStatus] = None


class KnowledgeSourceResponse(KnowledgeSourceBase, BaseTimestampedModel):
    """Schema for knowledge source responses"""
    id: str
    # File metadata
    file_name: Optional[str] = None
    file_extension: Optional[str] = None
    content_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_checksum: Optional[str] = None
    
    # Storage information
    storage_type: StorageType
    storage_provider: Optional[str] = None
    
    # Processing information
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    processing_attempts: int = 0
    content_extracted_at: Optional[datetime] = None
    
    # Content metadata
    content_summary: Optional[str] = None
    keywords: Optional[List[str]] = Field(default_factory=list)
    ai_insights: Optional[Dict[str, Any]] = None
    
    # Access and lifecycle
    upload_date: Optional[datetime] = None
    uploaded_by: Optional[str] = None
    account_id: str
    is_active: bool = True
    is_public: bool = False
    last_accessed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class KnowledgeSourceDetailResponse(KnowledgeSourceResponse):
    """Detailed schema for knowledge source with content"""
    extracted_text: Optional[str] = None
    content_sections: Optional[Dict[str, Any]] = None


class KnowledgeSourceSearchRequest(BaseModel):
    """Schema for knowledge source search requests"""
    query: Optional[str] = None
    category: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    file_types: Optional[List[str]] = Field(default_factory=list)  # Extensions: pdf, docx, etc.
    size_min: Optional[int] = None  # Minimum file size in bytes
    size_max: Optional[int] = None  # Maximum file size in bytes
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    processing_status: Optional[List[ProcessingStatus]] = Field(default_factory=list)
    specialty: Optional[List[str]] = Field(default_factory=list)
    access_level: Optional[List[AccessLevel]] = Field(default_factory=list)
    sort_by: str = Field(default="relevance", pattern="^(relevance|date|size|title|last_accessed)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class KnowledgeSourceSearchResponse(BaseModel):
    """Schema for knowledge source search responses"""
    items: List[KnowledgeSourceResponse]
    total: int
    has_more: bool
    facets: Dict[str, List[Dict[str, Union[str, int]]]] = Field(default_factory=dict)


class FileUploadRequest(BaseModel):
    """Schema for file upload requests"""
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    category: Optional[str] = None
    specialty: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    access_level: AccessLevel = AccessLevel.ACCOUNT


class FileUploadResponse(BaseModel):
    """Schema for file upload responses"""
    knowledge_source_id: str
    filename: str
    file_size_bytes: int
    content_type: str
    processing_status: ProcessingStatus
    upload_url: Optional[str] = None  # For direct upload scenarios


class DirectUploadRequest(BaseModel):
    """Schema for direct content upload requests"""
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: str = "text/plain"
    description: str
    category: Optional[str] = None
    specialty: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    access_level: AccessLevel = AccessLevel.ACCOUNT


class DirectUploadResponse(BaseModel):
    """Schema for direct upload URL responses"""
    upload_url: str
    knowledge_source_id: str
    fields: Optional[Dict[str, str]] = None  # Additional form fields for upload


class UploadCompleteRequest(BaseModel):
    """Schema for upload completion requests"""
    etag: Optional[str] = None
    final_size: Optional[int] = None


class ContentAnalysisResponse(BaseModel):
    """Schema for content analysis responses"""
    id: str
    content_summary: Optional[str] = None
    key_points: Optional[List[str]] = Field(default_factory=list)
    ai_insights: Optional[Dict[str, Any]] = None
    extracted_entities: Optional[Dict[str, List[str]]] = None
    sections: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    tables: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    confidence_score: float = 0.0


class ProcessingStatusResponse(BaseModel):
    """Schema for processing status responses"""
    processing_status: ProcessingStatus
    processing_attempts: int
    processing_error: Optional[str] = None
    content_extracted_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class FileDownloadResponse(BaseModel):
    """Schema for file download responses"""
    download_url: str
    expires_at: datetime
    filename: str
    content_type: str
    file_size_bytes: int


# Targeting Rule schemas
class TargetingRuleBase(BaseModel):
    """Base schema for targeting rules"""
    field: str = Field(..., min_length=1)
    operator: TargetingOperator
    value: Union[str, List[str], Dict[str, Any]]
    sequence: int = Field(..., ge=0)


class TargetingRuleCreate(TargetingRuleBase):
    """Schema for creating targeting rules"""
    pass


class TargetingRuleUpdate(BaseModel):
    """Schema for updating targeting rules"""
    field: Optional[str] = Field(None, min_length=1)
    operator: Optional[TargetingOperator] = None
    value: Optional[Union[str, List[str], Dict[str, Any]]] = None
    sequence: Optional[int] = Field(None, ge=0)


class TargetingRuleResponse(TargetingRuleBase):
    """Schema for targeting rule responses"""
    id: str
    strategy_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Outcome Action schemas
class OutcomeActionBase(BaseModel):
    """Base schema for outcome actions"""
    condition: OutcomeCondition
    action_type: OutcomeActionType
    details: Dict[str, Any] = Field(default_factory=dict)
    sequence: int = Field(..., ge=0)


class OutcomeActionCreate(OutcomeActionBase):
    """Schema for creating outcome actions"""
    pass


class OutcomeActionUpdate(BaseModel):
    """Schema for updating outcome actions"""
    condition: Optional[OutcomeCondition] = None
    action_type: Optional[OutcomeActionType] = None
    details: Optional[Dict[str, Any]] = None
    sequence: Optional[int] = Field(None, ge=0)


class OutcomeActionResponse(OutcomeActionBase):
    """Schema for outcome action responses"""
    id: str
    strategy_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Chat Strategy schemas
class ChatStrategyBase(BaseModel):
    """Base schema for chat strategies"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    goal: str
    patient_introduction: str
    specialty: Optional[StrategySpecialty] = None


class ChatStrategyCreate(ChatStrategyBase):
    """Schema for creating chat strategies"""
    knowledge_source_ids: List[str] = Field(default_factory=list)
    targeting_rules: List[TargetingRuleCreate] = Field(default_factory=list)
    outcome_actions: List[OutcomeActionCreate] = Field(default_factory=list)


class ChatStrategyUpdate(BaseModel):
    """Schema for updating chat strategies"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    goal: Optional[str] = None
    patient_introduction: Optional[str] = None
    specialty: Optional[StrategySpecialty] = None
    is_active: Optional[bool] = None


class ChatStrategyResponse(ChatStrategyBase, BaseTimestampedModel):
    """Schema for chat strategy responses"""
    id: str
    is_active: bool
    created_by: str
    account_id: str
    version: int
    knowledge_sources: List[KnowledgeSourceResponse] = Field(default_factory=list)
    targeting_rules: List[TargetingRuleResponse] = Field(default_factory=list)
    outcome_actions: List[OutcomeActionResponse] = Field(default_factory=list)


class ChatStrategyListResponse(BaseModel):
    """Schema for chat strategy list responses"""
    id: str
    name: str
    description: str
    is_active: bool
    specialty: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Strategy Execution schemas
class StrategyExecutionCreate(BaseModel):
    """Schema for creating strategy executions"""
    strategy_id: str
    patient_id: str
    trigger_criteria: Optional[Dict[str, Any]] = None


class StrategyExecutionResponse(BaseModel):
    """Schema for strategy execution responses"""
    id: str
    strategy_id: str
    session_id: Optional[str] = None
    patient_id: str
    triggered_by: Optional[str] = None
    trigger_criteria: Optional[Dict[str, Any]] = None
    execution_status: ExecutionStatus
    outcome_result: Optional[str] = None
    executed_actions: Optional[List[Dict[str, Any]]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Strategy Analytics schemas
class StrategyAnalyticsResponse(BaseModel):
    """Schema for strategy analytics responses"""
    id: str
    strategy_id: str
    date: date
    patients_screened: int
    criteria_met: int
    criteria_not_met: int
    incomplete_data: int
    avg_duration_minutes: Optional[int] = None
    tasks_created: int
    charts_flagged: int
    messages_sent: int
    followups_scheduled: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StrategyAnalyticsSummary(BaseModel):
    """Schema for strategy analytics summary"""
    total_patients_screened: int
    total_criteria_met: int
    total_criteria_not_met: int
    total_incomplete_data: int
    conversion_rate: float
    avg_duration_minutes: Optional[float] = None
    total_tasks_created: int
    total_charts_flagged: int
    total_messages_sent: int
    total_followups_scheduled: int
    date_range: Dict[str, date]


# Bulk operations schemas
class BulkKnowledgeSourceOperation(BaseModel):
    """Schema for bulk knowledge source operations"""
    knowledge_source_ids: List[str]
    operation: str = Field(..., pattern="^(delete|archive|activate|deactivate)$")


class BulkKnowledgeSourceUpdate(BaseModel):
    """Schema for bulk knowledge source updates"""
    knowledge_source_ids: List[str]
    updates: KnowledgeSourceUpdate


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation responses"""
    success_count: int
    error_count: int
    successful_ids: List[str] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)


class BulkStrategyOperation(BaseModel):
    """Schema for bulk strategy operations"""
    strategy_ids: List[str]
    operation: str = Field(..., pattern="^(activate|deactivate|delete)$")


# Strategy Template schemas
class StrategyTemplate(BaseModel):
    """Schema for strategy templates"""
    name: str
    description: str
    specialty: StrategySpecialty
    patient_introduction: str
    default_targeting_rules: List[Dict[str, Any]] = Field(default_factory=list)
    default_outcome_actions: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_duration: str
    target_criteria: List[str] = Field(default_factory=list)


# Patient targeting evaluation schemas
class PatientTargetingRequest(BaseModel):
    """Schema for patient targeting evaluation requests"""
    patient_id: str
    strategy_ids: Optional[List[str]] = None  # If None, evaluate all active strategies


class PatientTargetingResponse(BaseModel):
    """Schema for patient targeting evaluation responses"""
    patient_id: str
    applicable_strategies: List[str]
    evaluation_results: Dict[str, Dict[str, Any]]  # strategy_id -> evaluation details
