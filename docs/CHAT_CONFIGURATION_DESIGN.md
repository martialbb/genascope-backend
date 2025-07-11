# Chat Configuration Backend Design

## Overview

This document outlines the backend architecture and implementation plan for the Chat Configuration feature, which allows clinicians to create and manage AI-driven patient screening workflows.

## Current Backend Analysis

### Existing Structure
- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL
- **Architecture**: Repository pattern with services layer
- **Authentication**: JWT-based with role-based access control

### Current Chat System
The existing chat system provides:
- `ChatSession`: Tracks user conversations
- `ChatQuestion`: Static question templates
- `ChatAnswer`: User responses
- `RiskAssessment`: Eligibility and risk calculations

### Limitations of Current System
1. **Static Questions**: Questions are predefined and not configurable
2. **No Strategy Management**: No way to define reusable chat strategies
3. **Limited Targeting**: No patient targeting rules
4. **No Knowledge Integration**: No support for guidelines or custom knowledge
5. **Basic Outcomes**: Limited outcome actions and customization

## Proposed Chat Configuration Architecture

### 1. New Database Models

#### ChatStrategy
```sql
CREATE TABLE chat_strategies (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description TEXT,
    patient_introduction TEXT,
    is_active BOOLEAN DEFAULT false,
    specialty VARCHAR,
    created_by VARCHAR REFERENCES users(id),
    account_id VARCHAR REFERENCES accounts(id),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### KnowledgeSource (Hybrid Storage Architecture)
```sql
CREATE TABLE knowledge_sources (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR NOT NULL,
    type VARCHAR NOT NULL, -- 'guideline', 'research_paper', 'protocol', 'risk_model', 'custom_document', 'custom_link'
    url VARCHAR, -- For external links
    
    -- File Storage - Hybrid Approach (S3/MinIO + PostgreSQL Metadata)
    storage_type VARCHAR NOT NULL DEFAULT 's3', -- 's3', 'minio', 'database' (legacy)
    storage_provider VARCHAR, -- 'aws_s3', 'minio', 'gcp_storage', etc.
    s3_bucket VARCHAR, -- S3/MinIO bucket name
    s3_key VARCHAR, -- S3/MinIO object key/path
    s3_region VARCHAR, -- S3 region (if using AWS S3)
    s3_endpoint VARCHAR, -- Custom endpoint for MinIO/S3-compatible storage
    
    -- File Metadata
    file_name VARCHAR, -- Original filename
    file_extension VARCHAR, -- File extension (.pdf, .docx, etc.)
    content_type VARCHAR, -- MIME type
    file_size_bytes BIGINT, -- File size in bytes
    file_checksum VARCHAR, -- SHA256 hash for integrity verification
    file_encryption_key VARCHAR, -- Encryption key reference (if using client-side encryption)
    
    -- Content and AI Processing
    content_summary TEXT, -- AI-generated summary for search and display
    extracted_text TEXT, -- Full extracted text content (for search indexing)
    content_sections JSONB, -- Structured content sections with metadata
    search_vector tsvector, -- PostgreSQL full-text search vector
    ai_insights JSONB, -- AI-generated insights, key points, recommendations
    
    -- Classification and Organization
    version VARCHAR,
    category VARCHAR, -- 'clinical_guidelines', 'research', 'protocols', 'risk_assessment', 'custom'
    specialty VARCHAR, -- Medical specialty this relates to
    description TEXT,
    tags JSONB, -- Flexible tagging system for advanced filtering
    keywords JSONB, -- Extracted keywords for better searchability
    
    -- Processing and Status
    processing_status VARCHAR DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'retry'
    processing_error TEXT, -- Detailed error message if processing failed
    processing_attempts INTEGER DEFAULT 0, -- Number of processing attempts
    content_extracted_at TIMESTAMP, -- When content extraction completed
    last_accessed_at TIMESTAMP, -- For usage analytics and caching decisions
    
    -- Access Control and Audit
    upload_date TIMESTAMP DEFAULT NOW(),
    uploaded_by VARCHAR REFERENCES users(id),
    account_id VARCHAR REFERENCES accounts(id),
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false, -- Allow sharing across accounts (for templates)
    access_level VARCHAR DEFAULT 'account', -- 'account', 'user', 'public'
    
    -- Lifecycle Management
    retention_policy VARCHAR, -- 'permanent', 'archive_after_1_year', 'delete_after_2_years'
    archived_at TIMESTAMP, -- When file was archived (moved to cheaper storage)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints for data integrity
    CONSTRAINT chk_storage_consistency CHECK (
        (storage_type = 'database' AND content_summary IS NOT NULL) OR
        (storage_type IN ('s3', 'minio') AND s3_bucket IS NOT NULL AND s3_key IS NOT NULL)
    ),
    CONSTRAINT chk_processing_status CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed', 'retry')
    ),
    CONSTRAINT chk_access_level CHECK (
        access_level IN ('account', 'user', 'public')
    )
);

-- Optimized indexes for performance
CREATE INDEX idx_knowledge_sources_search ON knowledge_sources USING GIN(search_vector);
CREATE INDEX idx_knowledge_sources_tags ON knowledge_sources USING GIN(tags);
CREATE INDEX idx_knowledge_sources_keywords ON knowledge_sources USING GIN(keywords);
CREATE INDEX idx_knowledge_sources_account_active ON knowledge_sources(account_id, is_active);
CREATE INDEX idx_knowledge_sources_type_category ON knowledge_sources(type, category);
CREATE INDEX idx_knowledge_sources_processing_status ON knowledge_sources(processing_status);
CREATE INDEX idx_knowledge_sources_created_at ON knowledge_sources(created_at DESC);
```

#### StrategyKnowledgeSource (Junction Table)
```sql
CREATE TABLE strategy_knowledge_sources (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR REFERENCES chat_strategies(id) ON DELETE CASCADE,
    knowledge_source_id VARCHAR REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(strategy_id, knowledge_source_id)
);
```

#### TargetingRule
```sql
CREATE TABLE targeting_rules (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR REFERENCES chat_strategies(id) ON DELETE CASCADE,
    field VARCHAR NOT NULL, -- 'appointment_type', 'patient_age', 'diagnosis', etc.
    operator VARCHAR NOT NULL, -- 'is', 'is_not', 'is_between', 'contains', etc.
    value JSONB, -- Flexible value storage (string, array, object)
    sequence INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### OutcomeAction
```sql
CREATE TABLE outcome_actions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR REFERENCES chat_strategies(id) ON DELETE CASCADE,
    condition VARCHAR NOT NULL, -- 'meets_criteria', 'does_not_meet_criteria', 'incomplete_data'
    action_type VARCHAR NOT NULL, -- 'create_task', 'flag_chart', 'send_message', 'schedule_followup'
    details JSONB, -- Action-specific configuration
    sequence INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### StrategyExecution
```sql
CREATE TABLE strategy_executions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR REFERENCES chat_strategies(id),
    session_id VARCHAR REFERENCES chat_sessions(id),
    patient_id VARCHAR REFERENCES users(id),
    triggered_by VARCHAR REFERENCES users(id), -- Clinician who initiated
    trigger_criteria JSONB, -- Criteria that triggered this strategy
    execution_status VARCHAR DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    outcome_result VARCHAR, -- 'meets_criteria', 'does_not_meet_criteria', 'incomplete_data'
    executed_actions JSONB, -- Record of actions taken
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### StrategyAnalytics
```sql
CREATE TABLE strategy_analytics (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id VARCHAR REFERENCES chat_strategies(id),
    date DATE NOT NULL,
    patients_screened INTEGER DEFAULT 0,
    criteria_met INTEGER DEFAULT 0,
    criteria_not_met INTEGER DEFAULT 0,
    incomplete_data INTEGER DEFAULT 0,
    avg_duration_minutes INTEGER,
    tasks_created INTEGER DEFAULT 0,
    charts_flagged INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    followups_scheduled INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(strategy_id, date)
);
```

### 2. Enhanced Chat Models

#### Modified ChatSession
```sql
-- Add columns to existing chat_sessions table
ALTER TABLE chat_sessions ADD COLUMN strategy_id VARCHAR REFERENCES chat_strategies(id);
ALTER TABLE chat_sessions ADD COLUMN strategy_execution_id VARCHAR REFERENCES strategy_executions(id);
ALTER TABLE chat_sessions ADD COLUMN triggered_by_rules JSONB; -- Rules that triggered this session
```

#### Dynamic ChatQuestion
```sql
-- Add columns to existing chat_questions table
ALTER TABLE chat_questions ADD COLUMN strategy_id VARCHAR REFERENCES chat_strategies(id);
ALTER TABLE chat_questions ADD COLUMN knowledge_source_id VARCHAR REFERENCES knowledge_sources(id);
ALTER TABLE chat_questions ADD COLUMN is_dynamic BOOLEAN DEFAULT false; -- AI-generated vs. predefined
ALTER TABLE chat_questions ADD COLUMN context JSONB; -- Additional context for AI generation
```

### 3. API Endpoints

#### Strategy Management
```python
# GET /api/strategies - List all strategies for current user's account
# POST /api/strategies - Create new strategy
# GET /api/strategies/{id} - Get strategy details
# PUT /api/strategies/{id} - Update strategy
# DELETE /api/strategies/{id} - Delete strategy
# POST /api/strategies/{id}/activate - Activate/deactivate strategy
# POST /api/strategies/{id}/duplicate - Duplicate strategy
```

#### Enhanced Knowledge Sources API (Hybrid Storage)
```python
# File Upload and Management
POST /api/knowledge-sources/upload
Content-Type: multipart/form-data
Body: {
    file: File,
    title: string,
    description: string,
    category: string,
    tags: string[], // JSON array
    access_level: 'account' | 'user' | 'public'
}
Response: {
    id: string,
    title: string,
    file_name: string,
    file_size_bytes: number,
    content_type: string,
    processing_status: 'pending' | 'processing' | 'completed' | 'failed',
    upload_url: string, // Presigned URL for direct upload (optional)
    created_at: string
}

# Direct Upload (for large files)
POST /api/knowledge-sources/upload-url
Body: {
    file_name: string,
    content_type: string,
    file_size_bytes: number,
    title: string,
    description: string
}
Response: {
    upload_url: string, // Presigned URL for direct S3/MinIO upload
    knowledge_source_id: string,
    fields: object // Additional form fields for upload
}

# Complete direct upload
POST /api/knowledge-sources/{id}/upload-complete
Body: {
    etag: string,
    final_size: number
}
Response: {
    message: string,
    processing_status: string
}

# Advanced Search with Filters
GET /api/knowledge-sources/search
Query: {
    q: string, // Search query
    category: string[],
    tags: string[],
    file_type: string[], // Extensions: pdf, docx, etc.
    size_min: number, // Minimum file size in bytes
    size_max: number, // Maximum file size in bytes
    date_from: string, // ISO date
    date_to: string, // ISO date
    processing_status: string[],
    sort_by: 'relevance' | 'date' | 'size' | 'title',
    sort_order: 'asc' | 'desc',
    limit: number,
    offset: number
}
Response: {
    items: KnowledgeSource[],
    total: number,
    has_more: boolean,
    facets: {
        categories: { name: string, count: number }[],
        file_types: { type: string, count: number }[],
        tags: { tag: string, count: number }[]
    }
}

# Get File Content (Streaming)
GET /api/knowledge-sources/{id}/content
Query: {
    download: boolean, // Force download vs inline
    format: 'original' | 'text' | 'summary'
}
Response: Binary file content or text extraction
Headers: {
    'Content-Type': string,
    'Content-Disposition': 'attachment; filename="..."',
    'Content-Length': number,
    'X-Processing-Status': string
}

# Get Secure Download URL
GET /api/knowledge-sources/{id}/download-url
Query: {
    expires_in: number, // Seconds, max 7 days
    download: boolean
}
Response: {
    download_url: string,
    expires_at: string
}

# Bulk Operations
POST /api/knowledge-sources/bulk-delete
Body: {
    knowledge_source_ids: string[]
}
Response: {
    deleted: string[],
    failed: { id: string, error: string }[]
}

POST /api/knowledge-sources/bulk-update
Body: {
    knowledge_source_ids: string[],
    updates: {
        category?: string,
        tags?: string[],
        access_level?: string,
        is_active?: boolean
    }
}
Response: {
    updated: string[],
    failed: { id: string, error: string }[]
}

# Content Analysis
GET /api/knowledge-sources/{id}/analysis
Response: {
    id: string,
    content_summary: string,
    key_points: string[],
    ai_insights: {
        topics: string[],
        sentiment: string,
        complexity_score: number,
        recommendations: string[]
    },
    extracted_entities: {
        people: string[],
        organizations: string[],
        locations: string[],
        medical_terms: string[]
    },
    sections: object[],
    tables: object[],
    confidence_score: number
}

# Processing Status and Retry
GET /api/knowledge-sources/{id}/processing-status
Response: {
    processing_status: string,
    processing_attempts: number,
    processing_error: string | null,
    content_extracted_at: string | null,
    estimated_completion: string | null
}

POST /api/knowledge-sources/{id}/retry-processing
Response: {
    message: string,
    processing_status: string
}

# Usage Analytics
GET /api/knowledge-sources/analytics
Query: {
    date_from: string,
    date_to: string,
    account_id?: string, // Admin only
    group_by: 'day' | 'week' | 'month'
}
Response: {
    total_files: number,
    total_size_gb: number,
    processing_success_rate: number,
    avg_processing_time_minutes: number,
    usage_by_period: {
        period: string,
        uploads: number,
        downloads: number,
        total_size: number
    }[],
    top_categories: { category: string, count: number }[],
    file_type_distribution: { type: string, count: number, size_gb: number }[]
}

# Storage Management (Admin)
GET /api/admin/storage/usage
Response: {
    total_storage_gb: number,
    by_account: {
        account_id: string,
        account_name: string,
        file_count: number,
        storage_gb: number,
        last_upload: string
    }[],
    by_file_type: {
        extension: string,
        count: number,
        total_size_gb: number,
        avg_size_mb: number
    }[],
    processing_queue: {
        pending: number,
        processing: number,
        failed: number,
        avg_wait_time_minutes: number
    }
}

POST /api/admin/storage/cleanup
Body: {
    dry_run: boolean,
    criteria: {
        older_than_days: number,
        unused_for_days: number,
        failed_processing: boolean,
        account_ids?: string[]
    }
}
Response: {
    files_to_delete: number,
    size_to_free_gb: number,
    files_deleted?: number, // If not dry_run
    space_freed_gb?: number // If not dry_run
}

# File Sharing
POST /api/knowledge-sources/{id}/share
Body: {
    share_with: 'account' | 'user' | 'public',
    target_ids?: string[], // User/account IDs if specific sharing
    expires_at?: string,
    permissions: ['read', 'download']
}
Response: {
    share_id: string,
    share_url: string,
    expires_at: string
}

GET /api/knowledge-sources/shared/{share_id}
Response: KnowledgeSource // With limited fields based on permissions

# Version Management
POST /api/knowledge-sources/{id}/versions
Content-Type: multipart/form-data
Body: {
    file: File,
    version_notes: string
}
Response: {
    version_id: string,
    version_number: number,
    created_at: string
}

GET /api/knowledge-sources/{id}/versions
Response: {
    current_version: number,
    versions: {
        version_number: number,
        version_notes: string,
        file_size_bytes: number,
        created_at: string,
        created_by: string
    }[]
}

GET /api/knowledge-sources/{id}/versions/{version}/content
# Similar to main content endpoint but for specific version
```

#### Strategy Configuration
```python
# GET /api/strategies/{id}/targeting-rules - Get targeting rules
# POST /api/strategies/{id}/targeting-rules - Add targeting rule
# PUT /api/strategies/{id}/targeting-rules/{rule_id} - Update targeting rule
# DELETE /api/strategies/{id}/targeting-rules/{rule_id} - Delete targeting rule

# GET /api/strategies/{id}/outcome-actions - Get outcome actions
# POST /api/strategies/{id}/outcome-actions - Add outcome action
# PUT /api/strategies/{id}/outcome-actions/{action_id} - Update outcome action
# DELETE /api/strategies/{id}/outcome-actions/{action_id} - Delete outcome action
```

#### Strategy Execution & Analytics
```python
# POST /api/strategies/{id}/execute - Manually execute strategy for patient
# GET /api/strategies/{id}/executions - Get execution history
# GET /api/strategies/{id}/analytics - Get strategy analytics
# POST /api/strategies/{id}/test - Test strategy in sandbox mode
```

#### Enhanced Chat Endpoints
```python
# POST /api/chat/start-with-strategy - Start chat with specific strategy
# GET /api/chat/strategies/applicable - Get applicable strategies for patient
# POST /api/chat/evaluate-targeting - Evaluate if patient matches targeting rules
```

### 4. Service Layer Architecture

#### ChatStrategyService
```python
class ChatStrategyService(BaseService):
    def create_strategy(self, strategy_data: dict, user_id: str) -> ChatStrategy
    def update_strategy(self, strategy_id: str, updates: dict) -> ChatStrategy
    def activate_strategy(self, strategy_id: str, is_active: bool) -> ChatStrategy
    def get_applicable_strategies(self, patient_data: dict) -> List[ChatStrategy]
    def evaluate_targeting_rules(self, strategy: ChatStrategy, patient_data: dict) -> bool
    def execute_strategy(self, strategy_id: str, patient_id: str, triggered_by: str) -> StrategyExecution
    def record_analytics(self, execution: StrategyExecution) -> None
```

#### Enhanced KnowledgeSourceService (Hybrid Storage Implementation)
```python
import asyncio
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class UploadResult:
    bucket: str
    key: str
    size: int
    checksum: str
    url: Optional[str] = None
    region: Optional[str] = None
    content_type: Optional[str] = None

@dataclass
class FileValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    detected_type: Optional[str] = None
    estimated_size: Optional[int] = None

class KnowledgeSourceService(BaseService):
    def __init__(self, db: Session, storage_client: StorageClient, config: dict):
        self.db = db
        self.storage_client = storage_client
        self.content_processor = ContentProcessor()
        self.config = config
        self.max_file_size = config.get('max_file_size_bytes', 100 * 1024 * 1024)  # 100MB default
        self.allowed_extensions = config.get('allowed_extensions', ['.pdf', '.docx', '.doc', '.txt', '.md'])
        self.virus_scanner = VirusScanner() if config.get('enable_virus_scanning') else None
    
    async def create_knowledge_source(self, data: dict, user_id: str) -> KnowledgeSource:
        """Create a knowledge source (non-file based)"""
        knowledge_source_data = {
            **data,
            'uploaded_by': user_id,
            'storage_type': 'database',
            'processing_status': 'completed' if data.get('type') == 'custom_link' else 'pending'
        }
        
        knowledge_source = self.repository.create(knowledge_source_data)
        
        # For links, extract meta information
        if data.get('type') == 'custom_link' and data.get('url'):
            await self._process_link_metadata(knowledge_source.id, data['url'])
        
        return knowledge_source
    
    async def upload_document(self, file: UploadFile, metadata: dict, user_id: str) -> KnowledgeSource:
        """Upload document using hybrid storage approach with comprehensive validation"""
        try:
            # 1. Comprehensive file validation
            validation_result = await self._validate_file_comprehensive(file)
            if not validation_result.is_valid:
                raise ValueError(f"File validation failed: {validation_result.error_message}")
            
            # 2. Virus scanning (if enabled)
            if self.virus_scanner:
                scan_result = await self.virus_scanner.scan_file(file)
                if not scan_result.is_clean:
                    raise ValueError(f"File failed security scan: {scan_result.threat_info}")
            
            # 3. Generate unique identifiers and paths
            file_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime('%Y/%m/%d')
            s3_key = f"knowledge-sources/{metadata['account_id']}/{timestamp}/{file_id}/{file.filename}"
            
            # 4. Calculate file checksum
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            file_checksum = hashlib.sha256(file_content).hexdigest()
            
            # 5. Upload to S3/MinIO with error handling and retries
            upload_result = await self._upload_with_retry(
                file=file,
                bucket=self._get_bucket_name(metadata['account_id']),
                key=s3_key,
                content_type=validation_result.detected_type or file.content_type,
                checksum=file_checksum
            )
            
            # 6. Create database record with comprehensive metadata
            knowledge_source_data = {
                **metadata,
                'storage_type': self.config.get('default_storage_type', 's3'),
                'storage_provider': self.config.get('storage_provider', 'aws_s3'),
                's3_bucket': upload_result.bucket,
                's3_key': upload_result.key,
                's3_region': upload_result.region,
                's3_endpoint': self.config.get('storage_endpoint'),
                'file_name': file.filename,
                'file_extension': Path(file.filename).suffix.lower(),
                'content_type': upload_result.content_type,
                'file_size_bytes': upload_result.size,
                'file_checksum': upload_result.checksum,
                'processing_status': 'pending',
                'processing_attempts': 0,
                'uploaded_by': user_id,
                'upload_date': datetime.utcnow()
            }
            
            knowledge_source = self.repository.create(knowledge_source_data)
            
            # 7. Queue content extraction job
            await self._queue_content_extraction(knowledge_source.id)
            
            logger.info(f"Successfully uploaded knowledge source: {knowledge_source.id}")
            return knowledge_source
            
        except Exception as e:
            logger.error(f"Failed to upload document: {str(e)}")
            # Cleanup: remove from storage if database creation failed
            if 'upload_result' in locals():
                try:
                    await self.storage_client.delete_file(upload_result.bucket, upload_result.key)
                except:
                    pass  # Best effort cleanup
            raise
    
    async def extract_content(self, knowledge_source_id: str) -> None:
        """Background job for content extraction with retry logic"""
        knowledge_source = self.repository.get_by_id(knowledge_source_id)
        
        if not knowledge_source:
            logger.error(f"Knowledge source not found: {knowledge_source_id}")
            return
        
        try:
            # Update status and increment attempts
            self.repository.update(knowledge_source_id, {
                'processing_status': 'processing',
                'processing_attempts': knowledge_source.processing_attempts + 1
            })
            
            # Download file from S3/MinIO with timeout
            file_content = await asyncio.wait_for(
                self.storage_client.download_file(
                    bucket=knowledge_source.s3_bucket,
                    key=knowledge_source.s3_key
                ),
                timeout=300  # 5 minute timeout
            )
            
            # Extract text and metadata
            extraction_result = await self.content_processor.extract_content(
                file_content=file_content,
                content_type=knowledge_source.content_type,
                file_name=knowledge_source.file_name
            )
            
            # Generate AI insights if enabled
            ai_insights = {}
            if self.config.get('enable_ai_insights'):
                ai_insights = await self._generate_ai_insights(extraction_result.text)
            
            # Generate search vector and keywords
            search_text = f"{knowledge_source.title} {knowledge_source.description} {extraction_result.text}"
            search_vector = await self._generate_search_vector(search_text)
            keywords = await self._extract_keywords(extraction_result.text)
            
            # Update database with extracted content
            update_data = {
                'extracted_text': extraction_result.text,
                'content_summary': extraction_result.summary,
                'content_sections': extraction_result.sections,
                'ai_insights': ai_insights,
                'search_vector': search_vector,
                'keywords': keywords,
                'processing_status': 'completed',
                'content_extracted_at': datetime.utcnow(),
                'processing_error': None
            }
            
            self.repository.update(knowledge_source_id, update_data)
            
            logger.info(f"Successfully processed knowledge source: {knowledge_source_id}")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to process knowledge source {knowledge_source_id}: {error_message}")
            
            # Determine if we should retry
            should_retry = (
                knowledge_source.processing_attempts < 3 and
                not isinstance(e, (ValueError, TypeError))  # Don't retry validation errors
            )
            
            update_data = {
                'processing_status': 'retry' if should_retry else 'failed',
                'processing_error': error_message
            }
            
            self.repository.update(knowledge_source_id, update_data)
            
            # Schedule retry if applicable
            if should_retry:
                await asyncio.sleep(300)  # Wait 5 minutes before retry
                await self._queue_content_extraction(knowledge_source_id)
    
    async def search_knowledge_sources(
        self, 
        query: str, 
        account_id: str, 
        filters: dict = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Union[List[KnowledgeSource], int]]:
        """Advanced search with full-text search, filters, and pagination"""
        results = self.repository.search_content(
            query=query,
            account_id=account_id,
            filters=filters or {},
            limit=limit,
            offset=offset
        )
        
        # Update last_accessed_at for usage analytics
        if results['items']:
            knowledge_source_ids = [ks.id for ks in results['items']]
            await self._update_access_timestamps(knowledge_source_ids)
        
        return results
    
    async def get_file_content(self, knowledge_source_id: str, user_id: str) -> bytes:
        """Retrieve original file content from S3/MinIO with access control"""
        knowledge_source = self.repository.get_by_id(knowledge_source_id)
        
        # Access control check
        if not self._check_access_permission(knowledge_source, user_id):
            raise PermissionError("Insufficient permissions to access this file")
        
        # Update access timestamp
        await self._update_access_timestamps([knowledge_source_id])
        
        try:
            return await self.storage_client.download_file(
                bucket=knowledge_source.s3_bucket,
                key=knowledge_source.s3_key
            )
        except Exception as e:
            logger.error(f"Failed to download file {knowledge_source_id}: {str(e)}")
            raise
    
    async def get_file_download_url(
        self, 
        knowledge_source_id: str, 
        user_id: str,
        expires_in: int = 3600
    ) -> str:
        """Generate secure presigned URL for file download"""
        knowledge_source = self.repository.get_by_id(knowledge_source_id)
        
        # Access control check
        if not self._check_access_permission(knowledge_source, user_id):
            raise PermissionError("Insufficient permissions to access this file")
        
        # Generate presigned URL
        url = await self.storage_client.get_file_url(
            bucket=knowledge_source.s3_bucket,
            key=knowledge_source.s3_key,
            expires_in=expires_in
        )
        
        # Update access timestamp
        await self._update_access_timestamps([knowledge_source_id])
        
        return url
    
    async def delete_knowledge_source(self, knowledge_source_id: str, user_id: str) -> None:
        """Delete knowledge source and associated file with proper cleanup"""
        knowledge_source = self.repository.get_by_id(knowledge_source_id)
        
        # Permission check
        if not self._check_delete_permission(knowledge_source, user_id):
            raise PermissionError("Insufficient permissions to delete this knowledge source")
        
        try:
            # Delete from S3/MinIO
            if knowledge_source.storage_type in ['s3', 'minio']:
                await self.storage_client.delete_file(
                    bucket=knowledge_source.s3_bucket,
                    key=knowledge_source.s3_key
                )
            
            # Delete from database (cascade will handle related records)
            self.repository.delete(knowledge_source_id)
            
            logger.info(f"Successfully deleted knowledge source: {knowledge_source_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge source {knowledge_source_id}: {str(e)}")
            raise
    
    async def archive_knowledge_source(self, knowledge_source_id: str) -> None:
        """Archive knowledge source to cheaper storage tier"""
        knowledge_source = self.repository.get_by_id(knowledge_source_id)
        
        # Move to archive storage if supported by storage provider
        if hasattr(self.storage_client, 'archive_file'):
            await self.storage_client.archive_file(
                bucket=knowledge_source.s3_bucket,
                key=knowledge_source.s3_key
            )
        
        # Update database
        self.repository.update(knowledge_source_id, {
            'archived_at': datetime.utcnow(),
            'is_active': False
        })
    
    # Private helper methods
    async def _validate_file_comprehensive(self, file: UploadFile) -> FileValidationResult:
        """Comprehensive file validation including content inspection"""
        try:
            # Check file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                return FileValidationResult(
                    is_valid=False,
                    error_message=f"File type {file_ext} not allowed. Allowed types: {self.allowed_extensions}"
                )
            
            # Check file size
            file_size = 0
            content_peek = b""
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if len(content_peek) < 1024:  # Keep first 1KB for content detection
                    content_peek += chunk[:1024 - len(content_peek)]
                if file_size > self.max_file_size:
                    return FileValidationResult(
                        is_valid=False,
                        error_message=f"File size {file_size} exceeds limit of {self.max_file_size} bytes"
                    )
            
            await file.seek(0)  # Reset file pointer
            
            # Detect actual content type
            detected_type = mimetypes.guess_type(file.filename)[0]
            if not detected_type:
                detected_type = self._detect_content_type_from_content(content_peek)
            
            # Validate content type matches extension
            if not self._validate_content_type_consistency(file_ext, detected_type):
                return FileValidationResult(
                    is_valid=False,
                    error_message=f"File content doesn't match extension {file_ext}"
                )
            
            return FileValidationResult(
                is_valid=True,
                detected_type=detected_type,
                estimated_size=file_size
            )
            
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    async def _upload_with_retry(
        self, 
        file: UploadFile, 
        bucket: str, 
        key: str, 
        content_type: str,
        checksum: str,
        max_retries: int = 3
    ) -> UploadResult:
        """Upload file with retry logic"""
        for attempt in range(max_retries):
            try:
                return await self.storage_client.upload_file(
                    file=file,
                    bucket=bucket,
                    key=key,
                    content_type=content_type,
                    metadata={'checksum': checksum, 'upload_attempt': str(attempt + 1)}
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Upload attempt {attempt + 1} failed, retrying: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _get_bucket_name(self, account_id: str) -> str:
        """Get bucket name for account with environment-specific prefix"""
        env = self.config.get('environment', 'dev')
        return f"genascope-{env}-knowledge-{account_id}"
    
    def _check_access_permission(self, knowledge_source: KnowledgeSource, user_id: str) -> bool:
        """Check if user has permission to access knowledge source"""
        # Implementation depends on your access control model
        # This is a simplified version
        return (
            knowledge_source.access_level == 'public' or
            knowledge_source.uploaded_by == user_id or
            self._user_in_same_account(knowledge_source.account_id, user_id)
        )
    
    def _check_delete_permission(self, knowledge_source: KnowledgeSource, user_id: str) -> bool:
        """Check if user has permission to delete knowledge source"""
        return (
            knowledge_source.uploaded_by == user_id or
            self._user_is_admin(user_id, knowledge_source.account_id)
        )
    
    async def _queue_content_extraction(self, knowledge_source_id: str) -> None:
        """Queue background job for content extraction"""
        # Implementation depends on your job queue system (Celery, RQ, etc.)
        # For now, we'll call it directly in development
        if self.config.get('async_processing', False):
            asyncio.create_task(self.extract_content(knowledge_source_id))
        else:
            await self.extract_content(knowledge_source_id)
    
    async def _generate_ai_insights(self, text: str) -> dict:
        """Generate AI insights from extracted text"""
        # Placeholder for AI integration (OpenAI, etc.)
        return {
            "key_points": [],
            "recommendations": [],
            "risk_factors": [],
            "confidence_score": 0.0
        }
    
    async def _generate_search_vector(self, text: str) -> str:
        """Generate PostgreSQL tsvector for full-text search"""
        # This would be handled by PostgreSQL's to_tsvector function
        # Return the text for now, actual vector generation happens in the query
        return text
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for enhanced searchability"""
        # Simple keyword extraction - in production, use NLP libraries
        import re
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return list(set(words))[:20]  # Top 20 unique keywords
```

#### Enhanced StorageClient Architecture
```python
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Dict, Any
from dataclasses import dataclass
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class UploadResult:
    bucket: str
    key: str
    size: int
    checksum: str
    url: Optional[str] = None
    region: Optional[str] = None
    content_type: Optional[str] = None
    etag: Optional[str] = None
    version_id: Optional[str] = None

@dataclass 
class VirusScanResult:
    is_clean: bool
    threat_info: Optional[str] = None
    scan_engine: Optional[str] = None

class StorageClient(ABC):
    """Abstract storage client interface with async support"""
    
    @abstractmethod
    async def upload_file(
        self, 
        file: BinaryIO, 
        bucket: str, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        """Upload file to storage"""
        pass
    
    @abstractmethod
    async def download_file(self, bucket: str, key: str) -> bytes:
        """Download file from storage"""
        pass
    
    @abstractmethod
    async def delete_file(self, bucket: str, key: str) -> None:
        """Delete file from storage"""
        pass
    
    @abstractmethod
    async def get_file_url(
        self, 
        bucket: str, 
        key: str, 
        expires_in: int = 3600,
        response_content_disposition: Optional[str] = None
    ) -> str:
        """Generate presigned URL for file access"""
        pass
    
    @abstractmethod
    async def file_exists(self, bucket: str, key: str) -> bool:
        """Check if file exists"""
        pass
    
    @abstractmethod
    async def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get file metadata"""
        pass
    
    async def copy_file(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str) -> None:
        """Copy file within storage (default implementation via download/upload)"""
        content = await self.download_file(source_bucket, source_key)
        metadata = await self.get_file_metadata(source_bucket, source_key)
        
        from io import BytesIO
        await self.upload_file(
            file=BytesIO(content),
            bucket=dest_bucket,
            key=dest_key,
            content_type=metadata.get('content_type', 'application/octet-stream')
        )
    
    async def archive_file(self, bucket: str, key: str) -> None:
        """Archive file to cheaper storage tier (optional, not all providers support this)"""
        pass  # Default implementation does nothing

class S3StorageClient(StorageClient):
    """Enhanced AWS S3 storage client implementation"""
    
    def __init__(
        self, 
        aws_access_key: str, 
        aws_secret_key: str, 
        region: str,
        endpoint_url: Optional[str] = None,
        enable_encryption: bool = True,
        kms_key_id: Optional[str] = None
    ):
        import boto3
        from botocore.config import Config
        
        # Configure with retry and timeout settings
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60,
            connect_timeout=10
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            endpoint_url=endpoint_url,
            config=config
        )
        self.region = region
        self.enable_encryption = enable_encryption
        self.kms_key_id = kms_key_id
    
    async def upload_file(
        self, 
        file: BinaryIO, 
        bucket: str, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        import hashlib
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Calculate checksum
        file_content = await file.read() if hasattr(file, 'read') else file.read()
        if hasattr(file, 'seek'):
            await file.seek(0)  # Reset file pointer
        
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Prepare upload parameters
        upload_params = {
            'Bucket': bucket,
            'Key': key,
            'Body': file_content,
            'ContentType': content_type,
            'Metadata': metadata or {}
        }
        
        # Add encryption if enabled
        if self.enable_encryption:
            upload_params['ServerSideEncryption'] = 'AES256'
            if self.kms_key_id:
                upload_params['ServerSideEncryption'] = 'aws:kms'
                upload_params['SSEKMSKeyId'] = self.kms_key_id
        
        # Upload using thread pool for async operation
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: self.s3_client.put_object(**upload_params)
            )
        
        return UploadResult(
            bucket=bucket,
            key=key,
            size=len(file_content),
            checksum=checksum,
            region=self.region,
            content_type=content_type,
            etag=response.get('ETag', '').strip('"'),
            version_id=response.get('VersionId')
        )
    
    async def download_file(self, bucket: str, key: str) -> bytes:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: self.s3_client.get_object(Bucket=bucket, Key=key)
            )
        return response['Body'].read()
    
    async def delete_file(self, bucket: str, key: str) -> None:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: self.s3_client.delete_object(Bucket=bucket, Key=key)
            )
    
    async def get_file_url(
        self, 
        bucket: str, 
        key: str, 
        expires_in: int = 3600,
        response_content_disposition: Optional[str] = None
    ) -> str:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        params = {'Bucket': bucket, 'Key': key}
        if response_content_disposition:
            params['ResponseContentDisposition'] = response_content_disposition
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            url = await loop.run_in_executor(
                executor,
                lambda: self.s3_client.generate_presigned_url(
                    'get_object',
                    Params=params,
                    ExpiresIn=expires_in
                )
            )
        return url
    
    async def file_exists(self, bucket: str, key: str) -> bool:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from botocore.exceptions import ClientError
        
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    lambda: self.s3_client.head_object(Bucket=bucket, Key=key)
                )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    async def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: self.s3_client.head_object(Bucket=bucket, Key=key)
            )
        
        return {
            'content_type': response.get('ContentType'),
            'content_length': response.get('ContentLength'),
            'last_modified': response.get('LastModified'),
            'etag': response.get('ETag', '').strip('"'),
            'metadata': response.get('Metadata', {})
        }
    
    async def archive_file(self, bucket: str, key: str) -> None:
        """Move file to Glacier storage class"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: self.s3_client.copy_object(
                    Bucket=bucket,
                    Key=key,
                    CopySource={'Bucket': bucket, 'Key': key},
                    StorageClass='GLACIER',
                    MetadataDirective='COPY'
                )
            )

class MinIOStorageClient(StorageClient):
    """Enhanced MinIO storage client implementation"""
    
    def __init__(
        self, 
        endpoint: str, 
        access_key: str, 
        secret_key: str, 
        secure: bool = True,
        region: str = 'us-west-2'
    ):
        from minio import Minio
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region
        )
        self.region = region
    
    async def upload_file(
        self, 
        file: BinaryIO, 
        bucket: str, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        import hashlib
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from io import BytesIO
        
        # Ensure bucket exists
        await self._ensure_bucket_exists(bucket)
        
        # Calculate checksum
        file_content = await file.read() if hasattr(file, 'read') else file.read()
        if hasattr(file, 'seek'):
            await file.seek(0)  # Reset file pointer
        
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Upload using thread pool for async operation
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: self.client.put_object(
                    bucket,
                    key,
                    BytesIO(file_content),
                    length=len(file_content),
                    content_type=content_type,
                    metadata=metadata or {}
                )
            )
        
        return UploadResult(
            bucket=bucket,
            key=key,
            size=len(file_content),
            checksum=checksum,
            content_type=content_type,
            etag=result.etag.strip('"') if result.etag else None,
            version_id=result.version_id
        )
    
    async def download_file(self, bucket: str, key: str) -> bytes:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: self.client.get_object(bucket, key)
            )
        return response.read()
    
    async def delete_file(self, bucket: str, key: str) -> None:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: self.client.remove_object(bucket, key)
            )
    
    async def get_file_url(
        self, 
        bucket: str, 
        key: str, 
        expires_in: int = 3600,
        response_content_disposition: Optional[str] = None
    ) -> str:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from datetime import timedelta
        
        response_headers = {}
        if response_content_disposition:
            response_headers['response-content-disposition'] = response_content_disposition
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            url = await loop.run_in_executor(
                executor,
                lambda: self.client.presigned_get_object(
                    bucket, 
                    key, 
                    expires=timedelta(seconds=expires_in),
                    response_headers=response_headers if response_headers else None
                )
            )
        return url
    
    async def file_exists(self, bucket: str, key: str) -> bool:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from minio.error import S3Error
        
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    lambda: self.client.stat_object(bucket, key)
                )
            return True
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            raise
    
    async def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            stat = await loop.run_in_executor(
                executor,
                lambda: self.client.stat_object(bucket, key)
            )
        
        return {
            'content_type': stat.content_type,
            'content_length': stat.size,
            'last_modified': stat.last_modified,
            'etag': stat.etag.strip('"') if stat.etag else None,
            'metadata': stat.metadata or {}
        }
    
    async def _ensure_bucket_exists(self, bucket: str) -> None:
        """Ensure bucket exists, create if not"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            bucket_exists = await loop.run_in_executor(
                executor,
                lambda: self.client.bucket_exists(bucket)
            )
            
            if not bucket_exists:
                await loop.run_in_executor(
                    executor,
                    lambda: self.client.make_bucket(bucket, location=self.region)
                )

class LocalStorageClient(StorageClient):
    """Local filesystem storage client for development/testing"""
    
    def __init__(self, base_path: str):
        import os
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self, 
        file: BinaryIO, 
        bucket: str, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        import hashlib
        import json
        
        # Create directory structure
        file_path = self.base_path / bucket / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        file_content = await file.read() if hasattr(file, 'read') else file.read()
        file_path.write_bytes(file_content)
        
        # Write metadata
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        metadata_info = {
            'content_type': content_type,
            'metadata': metadata or {},
            'upload_time': datetime.utcnow().isoformat()
        }
        metadata_path.write_text(json.dumps(metadata_info))
        
        checksum = hashlib.sha256(file_content).hexdigest()
        
        return UploadResult(
            bucket=bucket,
            key=key,
            size=len(file_content),
            checksum=checksum,
            content_type=content_type
        )
    
    async def download_file(self, bucket: str, key: str) -> bytes:
        file_path = self.base_path / bucket / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_bytes()
    
    async def delete_file(self, bucket: str, key: str) -> None:
        file_path = self.base_path / bucket / key
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        
        if file_path.exists():
            file_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()
    
    async def get_file_url(
        self, 
        bucket: str, 
        key: str, 
        expires_in: int = 3600,
        response_content_disposition: Optional[str] = None
    ) -> str:
        # For local storage, return a file:// URL
        file_path = self.base_path / bucket / key
        return f"file://{file_path.absolute()}"
    
    async def file_exists(self, bucket: str, key: str) -> bool:
        file_path = self.base_path / bucket / key
        return file_path.exists()
    
    async def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        import json
        
        file_path = self.base_path / bucket / key
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        metadata = {}
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
        
        stat = file_path.stat()
        return {
            'content_type': metadata.get('content_type', 'application/octet-stream'),
            'content_length': stat.st_size,
            'last_modified': datetime.fromtimestamp(stat.st_mtime),
            'metadata': metadata.get('metadata', {})
        }

class VirusScanner:
    """Simple virus scanner interface (integrate with ClamAV, etc.)"""
    
    async def scan_file(self, file: BinaryIO) -> VirusScanResult:
        """Scan file for viruses (placeholder implementation)"""
        # In production, integrate with actual virus scanning service
        # For now, just return clean
        return VirusScanResult(
            is_clean=True,
            scan_engine='mock_scanner'
        )

# Storage client factory
def create_storage_client(config: dict) -> StorageClient:
    """Factory function to create appropriate storage client based on configuration"""
    storage_type = config.get('storage_type', 'local')
    
    if storage_type == 's3':
        return S3StorageClient(
            aws_access_key=config['aws_access_key'],
            aws_secret_key=config['aws_secret_key'],
            region=config['aws_region'],
            endpoint_url=config.get('s3_endpoint_url'),
            enable_encryption=config.get('enable_encryption', True),
            kms_key_id=config.get('kms_key_id')
        )
    elif storage_type == 'minio':
        return MinIOStorageClient(
            endpoint=config['minio_endpoint'],
            access_key=config['minio_access_key'],
            secret_key=config['minio_secret_key'],
            secure=config.get('minio_secure', True),
            region=config.get('minio_region', 'us-west-2')
        )
    elif storage_type == 'local':
        return LocalStorageClient(
            base_path=config.get('local_storage_path', './storage')
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
```

#### Enhanced ContentProcessor Service
```python
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Union
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ContentExtractionResult:
    text: str
    summary: str
    sections: Dict[str, Any]
    metadata: Dict[str, Any]
    key_points: List[str] = None
    tables: List[Dict[str, Any]] = None
    images_info: List[Dict[str, Any]] = None
    confidence_score: float = 0.0

@dataclass
class DocumentSection:
    title: str
    content: str
    level: int
    page_number: Optional[int] = None
    section_type: str = 'paragraph'  # 'heading', 'paragraph', 'table', 'list'

class ContentProcessor:
    """Enhanced service for extracting and processing content from various file types"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.max_text_length = self.config.get('max_text_length', 1_000_000)  # 1MB of text
        self.enable_ocr = self.config.get('enable_ocr', False)
        self.ai_service = self.config.get('ai_service')  # For advanced summarization
        
        # Initialize extractors
        self.extractors = {
            'application/pdf': self._extract_pdf,
            'application/msword': self._extract_doc,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._extract_docx,
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': self._extract_pptx,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': self._extract_xlsx,
            'text/plain': self._extract_text,
            'text/markdown': self._extract_markdown,
            'text/html': self._extract_html,
            'text/csv': self._extract_csv,
            'application/json': self._extract_json,
            'application/rtf': self._extract_rtf
        }
    
    async def extract_content(
        self, 
        file_content: bytes, 
        content_type: str,
        file_name: str = None
    ) -> ContentExtractionResult:
        """Extract content based on file type with enhanced processing"""
        if content_type not in self.extractors:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        try:
            extractor = self.extractors[content_type]
            result = await extractor(file_content, file_name or 'unknown')
            
            # Post-process the results
            result = await self._post_process_content(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Content extraction failed for {content_type}: {str(e)}")
            # Return basic result for fallback
            return ContentExtractionResult(
                text=f"Content extraction failed: {str(e)}",
                summary="Failed to extract content",
                sections={},
                metadata={"error": str(e), "content_type": content_type},
                confidence_score=0.0
            )
    
    async def _extract_pdf(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Enhanced PDF extraction with table and image detection"""
        try:
            from io import BytesIO
            import PyPDF2
            
            # Try PyPDF2 first for basic extraction
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(content))
                text_parts = []
                sections = {}
                
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(page_text)
                        sections[f"page_{i+1}"] = {
                            "content": page_text,
                            "page_number": i + 1,
                            "type": "page"
                        }
                
                full_text = "\n".join(text_parts)
                
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed, trying alternative methods: {e}")
                
                # Fallback to more robust extraction with pdfplumber
                try:
                    import pdfplumber
                    full_text, sections = await self._extract_pdf_with_pdfplumber(content)
                except ImportError:
                    logger.warning("pdfplumber not available, using basic extraction")
                    full_text = "PDF content extraction failed"
                    sections = {}
            
            # Generate summary and metadata
            summary = await self._generate_summary(full_text)
            key_points = await self._extract_key_points(full_text)
            
            metadata = {
                "pages": len(pdf_reader.pages) if 'pdf_reader' in locals() else 0,
                "file_type": "PDF",
                "estimated_reading_time": len(full_text.split()) // 200  # Assume 200 WPM
            }
            
            return ContentExtractionResult(
                text=full_text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                key_points=key_points,
                confidence_score=0.8 if full_text else 0.2
            )
            
        except Exception as e:
            raise ValueError(f"PDF extraction failed: {str(e)}")
    
    async def _extract_pdf_with_pdfplumber(self, content: bytes) -> tuple[str, dict]:
        """Extract PDF with table detection using pdfplumber"""
        import pdfplumber
        from io import BytesIO
        
        text_parts = []
        sections = {}
        tables = []
        
        with pdfplumber.open(BytesIO(content)) as pdf:
            for i, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                
                # Extract tables
                page_tables = page.extract_tables()
                for j, table in enumerate(page_tables):
                    if table:
                        tables.append({
                            "page": i + 1,
                            "table_index": j,
                            "data": table,
                            "rows": len(table),
                            "columns": len(table[0]) if table else 0
                        })
                
                sections[f"page_{i+1}"] = {
                    "content": page_text,
                    "page_number": i + 1,
                    "type": "page",
                    "tables_count": len(page_tables)
                }
        
        return "\n".join(text_parts), sections
    
    async def _extract_docx(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Enhanced DOCX extraction with structure preservation"""
        try:
            import docx
            from io import BytesIO
            
            doc = docx.Document(BytesIO(content))
            text_parts = []
            sections = {}
            tables = []
            current_section = {"title": "Document Start", "content": "", "level": 0}
            section_counter = 0
            
            for element in doc.element.body:
                if element.tag.endswith('p'):  # Paragraph
                    paragraph = docx.text.paragraph.Paragraph(element, doc)
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text)
                        
                        # Check if it's a heading
                        if paragraph.style.name.startswith('Heading'):
                            # Save previous section
                            if current_section["content"]:
                                sections[f"section_{section_counter}"] = current_section.copy()
                                section_counter += 1
                            
                            # Start new section
                            level = int(paragraph.style.name.replace('Heading ', ''))
                            current_section = {
                                "title": paragraph.text,
                                "content": "",
                                "level": level,
                                "type": "heading"
                            }
                        else:
                            current_section["content"] += paragraph.text + "\n"
                
                elif element.tag.endswith('tbl'):  # Table
                    table = docx.table.Table(element, doc)
                    table_data = []
                    for row in table.rows:
                        row_data = [cell.text.strip() for cell in row.cells]
                        table_data.append(row_data)
                    
                    if table_data:
                        tables.append({
                            "data": table_data,
                            "rows": len(table_data),
                            "columns": len(table_data[0]) if table_data else 0
                        })
                        
                        # Add table representation to text
                        table_text = "\n".join(["\t".join(row) for row in table_data])
                        text_parts.append(f"\n[TABLE]\n{table_text}\n[/TABLE]\n")
                        current_section["content"] += f"\n[Table with {len(table_data)} rows]\n"
            
            # Save final section
            if current_section["content"]:
                sections[f"section_{section_counter}"] = current_section
            
            full_text = "\n".join(text_parts)
            summary = await self._generate_summary(full_text)
            key_points = await self._extract_key_points(full_text)
            
            metadata = {
                "paragraphs": len([p for p in doc.paragraphs if p.text.strip()]),
                "tables": len(tables),
                "sections": len(sections),
                "file_type": "DOCX"
            }
            
            return ContentExtractionResult(
                text=full_text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                key_points=key_points,
                tables=tables,
                confidence_score=0.9
            )
            
        except Exception as e:
            raise ValueError(f"DOCX extraction failed: {str(e)}")
    
    async def _extract_xlsx(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from Excel files"""
        try:
            import openpyxl
            from io import BytesIO
            
            workbook = openpyxl.load_workbook(BytesIO(content), data_only=True)
            text_parts = []
            sections = {}
            tables = []
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_data = []
                
                for row in sheet.iter_rows(values_only=True):
                    if any(cell is not None for cell in row):
                        row_data = [str(cell) if cell is not None else "" for cell in row]
                        sheet_data.append(row_data)
                
                if sheet_data:
                    # Convert to text representation
                    sheet_text = "\n".join(["\t".join(row) for row in sheet_data])
                    text_parts.append(f"Sheet: {sheet_name}\n{sheet_text}")
                    
                    sections[f"sheet_{sheet_name}"] = {
                        "title": sheet_name,
                        "content": sheet_text,
                        "type": "spreadsheet",
                        "rows": len(sheet_data),
                        "columns": len(sheet_data[0]) if sheet_data else 0
                    }
                    
                    tables.append({
                        "sheet_name": sheet_name,
                        "data": sheet_data,
                        "rows": len(sheet_data),
                        "columns": len(sheet_data[0]) if sheet_data else 0
                    })
            
            full_text = "\n\n".join(text_parts)
            summary = await self._generate_summary(full_text)
            
            metadata = {
                "sheets": len(workbook.sheetnames),
                "total_tables": len(tables),
                "file_type": "XLSX"
            }
            
            return ContentExtractionResult(
                text=full_text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                tables=tables,
                confidence_score=0.85
            )
            
        except Exception as e:
            raise ValueError(f"XLSX extraction failed: {str(e)}")
    
    async def _extract_pptx(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from PowerPoint files"""
        try:
            from pptx import Presentation
            from io import BytesIO
            
            presentation = Presentation(BytesIO(content))
            text_parts = []
            sections = {}
            
            for i, slide in enumerate(presentation.slides):
                slide_text = []
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text)
                
                if slide_text:
                    slide_content = "\n".join(slide_text)
                    text_parts.append(slide_content)
                    
                    sections[f"slide_{i+1}"] = {
                        "title": slide_text[0] if slide_text else f"Slide {i+1}",
                        "content": slide_content,
                        "slide_number": i + 1,
                        "type": "slide"
                    }
            
            full_text = "\n\n".join(text_parts)
            summary = await self._generate_summary(full_text)
            key_points = await self._extract_key_points(full_text)
            
            metadata = {
                "slides": len(presentation.slides),
                "file_type": "PPTX"
            }
            
            return ContentExtractionResult(
                text=full_text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                key_points=key_points,
                confidence_score=0.8
            )
            
        except Exception as e:
            raise ValueError(f"PPTX extraction failed: {str(e)}")
    
    async def _extract_markdown(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Enhanced Markdown extraction with structure preservation"""
        try:
            import markdown
            from markdown.extensions import toc
            import re
            
            text = content.decode('utf-8')
            
            # Parse with markdown to get structure
            md = markdown.Markdown(extensions=['toc', 'tables', 'fenced_code'])
            html = md.convert(text)
            
            # Extract sections based on headers
            sections = {}
            current_section = {"title": "Introduction", "content": "", "level": 0}
            section_counter = 0
            
            lines = text.split('\n')
            for line in lines:
                header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                if header_match:
                    # Save previous section
                    if current_section["content"].strip():
                        sections[f"section_{section_counter}"] = current_section.copy()
                        section_counter += 1
                    
                    # Start new section
                    level = len(header_match.group(1))
                    title = header_match.group(2)
                    current_section = {
                        "title": title,
                        "content": "",
                        "level": level,
                        "type": "markdown_header"
                    }
                else:
                    current_section["content"] += line + "\n"
            
            # Save final section
            if current_section["content"].strip():
                sections[f"section_{section_counter}"] = current_section
            
            # Extract tables if present
            tables = []
            table_pattern = r'\|(.+)\|'
            table_lines = [line for line in lines if re.match(table_pattern, line)]
            if table_lines:
                # Simple table extraction
                table_data = []
                for line in table_lines:
                    if '---' not in line:  # Skip separator lines
                        cells = [cell.strip() for cell in line.split('|')[1:-1]]
                        table_data.append(cells)
                
                if table_data:
                    tables.append({
                        "data": table_data,
                        "rows": len(table_data),
                        "columns": len(table_data[0]) if table_data else 0,
                        "format": "markdown"
                    })
            
            summary = await self._generate_summary(text)
            key_points = await self._extract_key_points(text)
            
            metadata = {
                "html_length": len(html),
                "sections": len(sections),
                "tables": len(tables),
                "file_type": "Markdown"
            }
            
            return ContentExtractionResult(
                text=text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                key_points=key_points,
                tables=tables,
                confidence_score=0.95
            )
            
        except Exception as e:
            raise ValueError(f"Markdown extraction failed: {str(e)}")
    
    async def _extract_html(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from HTML files"""
        try:
            from bs4 import BeautifulSoup
            
            text = content.decode('utf-8')
            soup = BeautifulSoup(text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            full_text = soup.get_text()
            
            # Extract structured content
            sections = {}
            section_counter = 0
            
            # Find headers and content
            for i, header in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
                level = int(header.name[1])
                title = header.get_text().strip()
                
                # Get content until next header of same or higher level
                content_parts = []
                for sibling in header.next_siblings:
                    if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        sibling_level = int(sibling.name[1])
                        if sibling_level <= level:
                            break
                    if hasattr(sibling, 'get_text'):
                        content_parts.append(sibling.get_text())
                
                sections[f"section_{section_counter}"] = {
                    "title": title,
                    "content": "\n".join(content_parts),
                    "level": level,
                    "type": "html_header"
                }
                section_counter += 1
            
            # Extract tables
            tables = []
            for table in soup.find_all('table'):
                table_data = []
                for row in table.find_all('tr'):
                    row_data = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                    if row_data:
                        table_data.append(row_data)
                
                if table_data:
                    tables.append({
                        "data": table_data,
                        "rows": len(table_data),
                        "columns": len(table_data[0]) if table_data else 0,
                        "format": "html"
                    })
            
            summary = await self._generate_summary(full_text)
            
            metadata = {
                "html_tags": len(soup.find_all()),
                "sections": len(sections),
                "tables": len(tables),
                "file_type": "HTML"
            }
            
            return ContentExtractionResult(
                text=full_text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                tables=tables,
                confidence_score=0.9
            )
            
        except Exception as e:
            raise ValueError(f"HTML extraction failed: {str(e)}")
    
    async def _extract_text(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from plain text files"""
        try:
            text = content.decode('utf-8')
            
            # Simple section detection based on multiple newlines
            sections = {}
            paragraphs = text.split('\n\n')
            
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    sections[f"paragraph_{i}"] = {
                        "title": f"Paragraph {i+1}",
                        "content": paragraph.strip(),
                        "type": "paragraph"
                    }
            
            summary = await self._generate_summary(text)
            key_points = await self._extract_key_points(text)
            
            metadata = {
                "character_count": len(text),
                "word_count": len(text.split()),
                "paragraphs": len(paragraphs),
                "file_type": "Plain Text"
            }
            
            return ContentExtractionResult(
                text=text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                key_points=key_points,
                confidence_score=1.0
            )
            
        except Exception as e:
            raise ValueError(f"Text extraction failed: {str(e)}")
    
    async def _extract_csv(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from CSV files"""
        try:
            import csv
            from io import StringIO
            
            text = content.decode('utf-8')
            csv_reader = csv.reader(StringIO(text))
            
            rows = list(csv_reader)
            if not rows:
                raise ValueError("Empty CSV file")
            
            # Convert to text representation
            text_representation = "\n".join(["\t".join(row) for row in rows])
            
            # Create structured representation
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            sections = {
                "csv_data": {
                    "title": f"CSV Data - {file_name}",
                    "content": text_representation,
                    "type": "csv_table",
                    "headers": headers,
                    "data_rows": len(data_rows)
                }
            }
            
            tables = [{
                "data": rows,
                "rows": len(rows),
                "columns": len(headers),
                "headers": headers,
                "format": "csv"
            }]
            
            summary = f"CSV file with {len(headers)} columns and {len(data_rows)} data rows"
            
            metadata = {
                "rows": len(rows),
                "columns": len(headers),
                "has_headers": True,
                "file_type": "CSV"
            }
            
            return ContentExtractionResult(
                text=text_representation,
                summary=summary,
                sections=sections,
                metadata=metadata,
                tables=tables,
                confidence_score=0.95
            )
            
        except Exception as e:
            raise ValueError(f"CSV extraction failed: {str(e)}")
    
    async def _extract_json(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from JSON files"""
        try:
            import json
            
            text = content.decode('utf-8')
            data = json.loads(text)
            
            # Convert JSON to readable text
            text_representation = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Create summary based on structure
            def analyze_json_structure(obj, path=""):
                if isinstance(obj, dict):
                    return f"Object with {len(obj)} keys: {', '.join(list(obj.keys())[:5])}"
                elif isinstance(obj, list):
                    return f"Array with {len(obj)} items"
                else:
                    return f"Value: {str(obj)[:50]}"
            
            summary = f"JSON data: {analyze_json_structure(data)}"
            
            sections = {
                "json_structure": {
                    "title": f"JSON Structure - {file_name}",
                    "content": text_representation,
                    "type": "json_data"
                }
            }
            
            metadata = {
                "json_type": type(data).__name__,
                "file_type": "JSON"
            }
            
            if isinstance(data, dict):
                metadata["keys"] = len(data)
            elif isinstance(data, list):
                metadata["items"] = len(data)
            
            return ContentExtractionResult(
                text=text_representation,
                summary=summary,
                sections=sections,
                metadata=metadata,
                confidence_score=1.0
            )
            
        except Exception as e:
            raise ValueError(f"JSON extraction failed: {str(e)}")
    
    async def _extract_rtf(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from RTF files"""
        try:
            # Basic RTF extraction - remove RTF formatting codes
            text = content.decode('utf-8', errors='ignore')
            
            # Remove RTF control codes (simplified)
            import re
            text = re.sub(r'\\[a-z]+\d*', '', text)  # Remove control words
            text = re.sub(r'[{}]', '', text)  # Remove braces
            text = re.sub(r'\\\w+', '', text)  # Remove remaining backslash commands
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            
            summary = await self._generate_summary(text)
            
            sections = {
                "rtf_content": {
                    "title": f"RTF Content - {file_name}",
                    "content": text,
                    "type": "rtf_document"
                }
            }
            
            metadata = {
                "file_type": "RTF",
                "word_count": len(text.split())
            }
            
            return ContentExtractionResult(
                text=text,
                summary=summary,
                sections=sections,
                metadata=metadata,
                confidence_score=0.7  # Lower confidence due to basic extraction
            )
            
        except Exception as e:
            raise ValueError(f"RTF extraction failed: {str(e)}")
    
    async def _extract_doc(self, content: bytes, file_name: str) -> ContentExtractionResult:
        """Extract content from legacy DOC files"""
        try:
            # Note: This requires python-docx2txt or similar library
            # For now, we'll return a placeholder
            text = "Legacy DOC format - content extraction requires additional dependencies"
            
            sections = {
                "doc_placeholder": {
                    "title": f"DOC File - {file_name}",
                    "content": text,
                    "type": "doc_legacy"
                }
            }
            
            metadata = {
                "file_type": "DOC (Legacy)",
                "extraction_note": "Requires additional libraries for full extraction"
            }
            
            return ContentExtractionResult(
                text=text,
                summary="Legacy DOC file detected",
                sections=sections,
                metadata=metadata,
                confidence_score=0.1
            )
            
        except Exception as e:
            raise ValueError(f"DOC extraction failed: {str(e)}")
    
    async def _post_process_content(self, result: ContentExtractionResult) -> ContentExtractionResult:
        """Post-process extracted content for quality and consistency"""
        
        # Truncate text if too long
        if len(result.text) > self.max_text_length:
            result.text = result.text[:self.max_text_length] + "... [Content truncated]"
            result.metadata["truncated"] = True
        
        # Enhance summary if AI service is available
        if self.ai_service and len(result.text) > 500:
            try:
                enhanced_summary = await self._generate_ai_summary(result.text)
                if enhanced_summary:
                    result.summary = enhanced_summary
                    result.confidence_score = min(result.confidence_score + 0.1, 1.0)
            except Exception as e:
                logger.warning(f"AI summary generation failed: {e}")
        
        # Ensure summary is not too long
        if len(result.summary) > 1000:
            result.summary = result.summary[:1000] + "..."
        
        return result
    
    async def _generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of the text (basic implementation)"""
        if not text.strip():
            return "Empty content"
        
        # Basic extractive summarization
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not sentences:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Take first few sentences up to max_length
        summary_parts = []
        current_length = 0
        
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            if current_length + len(sentence) < max_length:
                summary_parts.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        summary = ". ".join(summary_parts)
        if summary and not summary.endswith('.'):
            summary += "."
        
        return summary or text[:max_length] + "..."
    
    async def _extract_key_points(self, text: str, max_points: int = 10) -> List[str]:
        """Extract key points from text (basic implementation)"""
        if not text.strip():
            return []
        
        # Simple approach: find sentences with key phrases
        key_phrases = ['important', 'significant', 'key', 'critical', 'essential', 'main', 'primary']
        
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        key_points = []
        
        for sentence in sentences:
            if any(phrase in sentence.lower() for phrase in key_phrases):
                if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                    key_points.append(sentence + ".")
                    if len(key_points) >= max_points:
                        break
        
        # If no key phrases found, take first few substantive sentences
        if not key_points:
            key_points = [s + "." for s in sentences[:3] if len(s) > 20]
        
        return key_points
    
    async def _generate_ai_summary(self, text: str) -> Optional[str]:
        """Generate AI-powered summary (placeholder for AI integration)"""
        # This would integrate with OpenAI, Anthropic, or other AI services
        # For now, return None to use basic summarization
        return None
```

#### EnhancedChatService
```python
class EnhancedChatService(ChatService):
    def start_strategy_chat(self, strategy_id: str, patient_id: str, triggered_by: str) -> ChatSession
    def generate_dynamic_questions(self, strategy: ChatStrategy, patient_data: dict) -> List[ChatQuestion]
    def evaluate_outcome(self, execution: StrategyExecution) -> str
    def execute_outcome_actions(self, execution: StrategyExecution, outcome: str) -> List[dict]
```

#### TargetingEngineService
```python
class TargetingEngineService(BaseService):
    def evaluate_rules(self, rules: List[TargetingRule], patient_data: dict) -> bool
    def apply_operator(self, field_value: Any, operator: str, rule_value: Any) -> bool
    def get_patient_data(self, patient_id: str) -> dict
    def schedule_automated_execution(self) -> None  # Background job for rule evaluation
```

### 5. Repository Layer

#### ChatStrategyRepository
```python
class ChatStrategyRepository(BaseRepository):
    def get_by_account(self, account_id: str) -> List[ChatStrategy]
    def get_active_strategies(self, account_id: str) -> List[ChatStrategy]
    def get_with_knowledge_sources(self, strategy_id: str) -> ChatStrategy
    def get_with_targeting_rules(self, strategy_id: str) -> ChatStrategy
    def get_with_outcome_actions(self, strategy_id: str) -> ChatStrategy
```

#### KnowledgeSourceRepository
```python
class KnowledgeSourceRepository(BaseRepository):
    def get_by_account(self, account_id: str) -> List[KnowledgeSource]
    def get_by_type(self, knowledge_type: str, account_id: str) -> List[KnowledgeSource]
    def search_content(self, query: str, account_id: str) -> List[KnowledgeSource]
```

### 6. Pydantic Schemas

#### Request/Response Schemas
```python
class ChatStrategyCreate(BaseModel):
    name: str
    description: str
    patient_introduction: str
    specialty: Optional[str] = None

class ChatStrategyResponse(BaseModel):
    id: str
    name: str
    description: str
    patient_introduction: str
    is_active: bool
    specialty: Optional[str] = None
    created_by: str
    created_at: datetime
    knowledge_sources: List[KnowledgeSourceResponse] = []
    targeting_rules: List[TargetingRuleResponse] = []
    outcome_actions: List[OutcomeActionResponse] = []

class KnowledgeSourceCreate(BaseModel):
    title: str
    type: str
    url: Optional[str] = None
    description: str
    category: Optional[str] = None

class TargetingRuleCreate(BaseModel):
    field: str
    operator: str
    value: Union[str, List[str], dict]

class OutcomeActionCreate(BaseModel):
    condition: str
    action_type: str
    details: dict
```

### 7. Migration Plan

#### Phase 1: Core Models
1. Create new tables for chat strategies, knowledge sources, targeting rules, outcome actions
2. Add foreign keys to existing chat tables
3. Create junction tables for many-to-many relationships

#### Phase 2: API Implementation
1. Implement strategy CRUD operations
2. Add knowledge source management
3. Build targeting rule engine
4. Create outcome action execution

#### Phase 3: Integration
1. Enhance existing chat service to use strategies
2. Implement automated rule evaluation
3. Add analytics collection
4. Build reporting dashboard

#### Phase 4: Advanced Features
1. AI-powered question generation
2. Content extraction from documents
3. Advanced analytics and insights
4. Template library and sharing

### 8. Security Considerations

#### Access Control
- Strategies are scoped to accounts (multi-tenancy)
- Role-based permissions (admins and clinicians can create/edit)
- Patients can only execute strategies, not configure them

#### Data Privacy
- Patient data used in targeting is anonymized in logs
- Knowledge sources may contain PHI - proper access controls required
- Audit trail for all strategy executions and modifications

#### File Upload Security
- Virus scanning for uploaded documents
- File type validation and size limits
- Secure storage with encrypted at rest
- Content extraction in sandboxed environment

### 9. Performance Optimization

#### Caching Strategy
- Cache active strategies per account
- Cache compiled targeting rules
- Cache knowledge source content for AI generation

#### Background Jobs
- Automated rule evaluation for new patients/appointments
- Analytics aggregation (daily/weekly/monthly)
- Content indexing for knowledge sources
- Cleanup of old strategy executions

#### Database Optimization
- Indexes on frequently queried fields (strategy_id, patient_id, date)
- Partitioning of analytics tables by date
- Archival strategy for old executions

### 10. Hybrid Storage Configuration & Deployment

#### Configuration Management
```python
# config/storage.py
from typing import Dict, Any
import os
from enum import Enum

class StorageProvider(Enum):
    LOCAL = "local"
    AWS_S3 = "aws_s3"
    MINIO = "minio"
    GCP_STORAGE = "gcp_storage"

class StorageConfig:
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load storage configuration based on environment"""
        base_config = {
            "max_file_size_bytes": 100 * 1024 * 1024,  # 100MB
            "allowed_extensions": [".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".pptx"],
            "enable_virus_scanning": False,
            "enable_ai_insights": False,
            "async_processing": True,
            "retention_days": 2555,  # 7 years default
        }
        
        if self.environment == "development":
            return {
                **base_config,
                "storage_type": StorageProvider.LOCAL.value,
                "local_storage_path": "./storage/development",
                "enable_virus_scanning": False,
            }
        
        elif self.environment == "testing":
            return {
                **base_config,
                "storage_type": StorageProvider.LOCAL.value,
                "local_storage_path": "./storage/testing",
                "max_file_size_bytes": 10 * 1024 * 1024,  # 10MB for tests
            }
        
        elif self.environment == "staging":
            return {
                **base_config,
                "storage_type": StorageProvider.MINIO.value,
                "minio_endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                "minio_access_key": os.getenv("MINIO_ACCESS_KEY"),
                "minio_secret_key": os.getenv("MINIO_SECRET_KEY"),
                "minio_secure": os.getenv("MINIO_SECURE", "false").lower() == "true",
                "enable_virus_scanning": True,
            }
        
        elif self.environment == "production":
            return {
                **base_config,
                "storage_type": StorageProvider.AWS_S3.value,
                "aws_access_key": os.getenv("AWS_ACCESS_KEY_ID"),
                "aws_secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "aws_region": os.getenv("AWS_REGION", "us-west-2"),
                "enable_encryption": True,
                "kms_key_id": os.getenv("AWS_KMS_KEY_ID"),
                "enable_virus_scanning": True,
                "enable_ai_insights": True,
                "backup_to_glacier": True,
            }
        
        else:
            raise ValueError(f"Unknown environment: {self.environment}")
    
    def get_storage_client(self):
        """Factory method to create storage client"""
        from services.storage import create_storage_client
        return create_storage_client(self.config)

# config/database.py
def get_database_migration_for_storage():
    """Additional database configurations for hybrid storage"""
    return """
    -- Additional indexes for performance with large file datasets
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_sources_size_status 
    ON knowledge_sources(file_size_bytes, processing_status) 
    WHERE storage_type IN ('s3', 'minio');
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_sources_retention 
    ON knowledge_sources(upload_date, retention_policy) 
    WHERE is_active = true;
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_sources_access_frequency 
    ON knowledge_sources(last_accessed_at DESC, account_id) 
    WHERE is_active = true;
    
    -- Partial indexes for file processing
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_sources_failed_processing 
    ON knowledge_sources(processing_error, processing_attempts) 
    WHERE processing_status = 'failed';
    
    -- Index for analytics queries
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_sources_analytics 
    ON knowledge_sources(account_id, upload_date, file_extension) 
    WHERE is_active = true;
    """
```

#### Docker Configuration
```yaml
# docker-compose.storage.yml
version: '3.8'

services:
  # MinIO for development/staging
  minio:
    image: minio/minio:latest
    container_name: genascope-minio
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
      MINIO_BROWSER_REDIRECT_URL: http://localhost:9001
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - genascope-network

  # Redis for caching and job queue
  redis:
    image: redis:7-alpine
    container_name: genascope-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - genascope-network

  # Background worker for content processing
  worker:
    build: .
    container_name: genascope-worker
    depends_on:
      - postgres
      - redis
      - minio
    environment:
      - DATABASE_URL=postgresql://genascope:password@postgres:5432/genascope
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin123
      - WORKER_MODE=true
    volumes:
      - ./logs:/app/logs
    command: python -m app.workers.content_processor
    networks:
      - genascope-network

volumes:
  minio_data:
  redis_data:

networks:
  genascope-network:
    external: true
```

#### Environment Variables Template
```bash
# .env.production
# Storage Configuration
STORAGE_TYPE=aws_s3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2
AWS_KMS_KEY_ID=your_kms_key_id

# File Processing
MAX_FILE_SIZE_BYTES=104857600
ENABLE_VIRUS_SCANNING=true
ENABLE_AI_INSIGHTS=true
ASYNC_PROCESSING=true

# Content Processing
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
DATADOG_API_KEY=your_datadog_key

# .env.staging
STORAGE_TYPE=minio
MINIO_ENDPOINT=your_minio_endpoint:9000
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
MINIO_SECURE=true

# .env.development
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage/development
ENABLE_VIRUS_SCANNING=false
ENABLE_AI_INSIGHTS=false
```

#### Background Job Configuration
```python
# app/workers/content_processor.py
import asyncio
import logging
from celery import Celery
from app.core.config import get_settings
from app.services.knowledge_source import KnowledgeSourceService
from app.core.database import get_db_session

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure Celery for background processing
celery_app = Celery(
    "genascope_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.content_processor"]
)

# Configure task routing
celery_app.conf.update(
    task_routes={
        "app.workers.content_processor.process_knowledge_source": {"queue": "content_processing"},
        "app.workers.content_processor.cleanup_old_files": {"queue": "maintenance"},
        "app.workers.content_processor.generate_analytics": {"queue": "analytics"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

@celery_app.task(bind=True, max_retries=3)
def process_knowledge_source(self, knowledge_source_id: str):
    """Background task for processing uploaded knowledge sources"""
    try:
        with get_db_session() as db:
            storage_config = StorageConfig(settings.ENVIRONMENT)
            storage_client = storage_config.get_storage_client()
            
            service = KnowledgeSourceService(
                db=db,
                storage_client=storage_client,
                config=storage_config.config
            )
            
            asyncio.run(service.extract_content(knowledge_source_id))
            logger.info(f"Successfully processed knowledge source: {knowledge_source_id}")
            
    except Exception as exc:
        logger.error(f"Failed to process knowledge source {knowledge_source_id}: {str(exc)}")
        
        # Retry with exponential backoff
        retry_delay = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=retry_delay)

@celery_app.task
def cleanup_old_files():
    """Cleanup old files based on retention policy"""
    from datetime import datetime, timedelta
    
    with get_db_session() as db:
        storage_config = StorageConfig(settings.ENVIRONMENT)
        storage_client = storage_config.get_storage_client()
        
        service = KnowledgeSourceService(
            db=db,
            storage_client=storage_client,
            config=storage_config.config
        )
        
        # Find files older than retention period
        cutoff_date = datetime.utcnow() - timedelta(days=storage_config.config.get('retention_days', 2555))
        old_files = service.repository.get_files_older_than(cutoff_date)
        
        for file in old_files:
            try:
                asyncio.run(service.archive_knowledge_source(file.id))
                logger.info(f"Archived old file: {file.id}")
            except Exception as e:
                logger.error(f"Failed to archive file {file.id}: {str(e)}")

@celery_app.task
def generate_usage_analytics():
    """Generate analytics for file usage and storage"""
    with get_db_session() as db:
        # Implementation for analytics generation
        pass

# Periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.workers.content_processor.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'generate-analytics': {
        'task': 'app.workers.content_processor.generate_usage_analytics',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}

if __name__ == "__main__":
    celery_app.start()
```

#### Monitoring and Alerting
```python
# app/monitoring/storage_monitor.py
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.metrics import MetricsCollector

class StorageMonitor:
    def __init__(self, storage_client, db_session):
        self.storage_client = storage_client
        self.db = db_session
        self.metrics = MetricsCollector()
        self.logger = logging.getLogger(__name__)
    
    async def collect_storage_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive storage metrics"""
        metrics = {}
        
        try:
            # Database metrics
            metrics.update(await self._collect_database_metrics())
            
            # Storage service metrics
            metrics.update(await self._collect_storage_service_metrics())
            
            # Processing metrics
            metrics.update(await self._collect_processing_metrics())
            
            # Cost metrics (for cloud storage)
            metrics.update(await self._collect_cost_metrics())
            
            # Send to monitoring service
            self.metrics.send_metrics("storage_health", metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect storage metrics: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database-related metrics"""
        query = """
        SELECT 
            COUNT(*) as total_files,
            COUNT(*) FILTER (WHERE processing_status = 'completed') as processed_files,
            COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_files,
            COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_files,
            SUM(file_size_bytes) as total_size_bytes,
            AVG(file_size_bytes) as avg_file_size,
            COUNT(DISTINCT account_id) as active_accounts,
            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as files_last_24h
        FROM knowledge_sources 
        WHERE is_active = true
        """
        
        result = self.db.execute(query).fetchone()
        
        return {
            "db_total_files": result.total_files,
            "db_processed_files": result.processed_files,
            "db_failed_files": result.failed_files,
            "db_pending_files": result.pending_files,
            "db_total_size_gb": result.total_size_bytes / (1024**3) if result.total_size_bytes else 0,
            "db_avg_file_size_mb": result.avg_file_size / (1024**2) if result.avg_file_size else 0,
            "db_active_accounts": result.active_accounts,
            "db_files_last_24h": result.files_last_24h
        }
    
    async def _collect_storage_service_metrics(self) -> Dict[str, Any]:
        """Collect storage service health metrics"""
        metrics = {}
        
        try:
            # Test storage connectivity
            test_bucket = "health-check"
            test_key = f"health-check-{datetime.utcnow().isoformat()}"
            
            start_time = datetime.utcnow()
            
            # Upload test
            await self.storage_client.upload_file(
                file=BytesIO(b"health check"),
                bucket=test_bucket,
                key=test_key,
                content_type="text/plain"
            )
            
            upload_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Download test
            start_time = datetime.utcnow()
            await self.storage_client.download_file(test_bucket, test_key)
            download_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Cleanup
            await self.storage_client.delete_file(test_bucket, test_key)
            
            metrics.update({
                "storage_service_available": True,
                "storage_upload_latency_ms": upload_time * 1000,
                "storage_download_latency_ms": download_time * 1000
            })
            
        except Exception as e:
            metrics.update({
                "storage_service_available": False,
                "storage_service_error": str(e)
            })
        
        return metrics
    
    async def _collect_processing_metrics(self) -> Dict[str, Any]:
        """Collect content processing metrics"""
        query = """
        SELECT 
            AVG(EXTRACT(EPOCH FROM (content_extracted_at - created_at))) as avg_processing_time_seconds,
            COUNT(*) FILTER (WHERE processing_attempts > 1) as retry_count,
            COUNT(*) FILTER (WHERE processing_status = 'processing' AND created_at < NOW() - INTERVAL '1 hour') as stuck_processing
        FROM knowledge_sources 
        WHERE processing_status IN ('completed', 'failed', 'processing')
        AND created_at > NOW() - INTERVAL '24 hours'
        """
        
        result = self.db.execute(query).fetchone()
        
        return {
            "processing_avg_time_minutes": result.avg_processing_time_seconds / 60 if result.avg_processing_time_seconds else 0,
            "processing_retry_count": result.retry_count or 0,
            "processing_stuck_files": result.stuck_processing or 0
        }
    
    async def _collect_cost_metrics(self) -> Dict[str, Any]:
        """Collect cost-related metrics (for cloud storage)"""
        # This would integrate with cloud provider billing APIs
        # For now, estimate based on storage usage
        
        query = """
        SELECT 
            SUM(file_size_bytes) as total_storage_bytes,
            COUNT(*) as total_requests_estimate
        FROM knowledge_sources 
        WHERE is_active = true
        """
        
        result = self.db.execute(query).fetchone()
        
        # Rough cost estimation (adjust based on actual provider pricing)
        storage_gb = result.total_storage_bytes / (1024**3) if result.total_storage_bytes else 0
        estimated_monthly_cost = storage_gb * 0.023  # Rough S3 standard pricing
        
        return {
            "estimated_monthly_storage_cost_usd": estimated_monthly_cost,
            "total_storage_gb": storage_gb
        }
```

#### File Storage Integration for Knowledge Sources

### S3 Integration for Knowledge Base Files

The Chat Configuration system integrates with AWS S3 for secure storage of knowledge sources such as:
- Medical guidelines and protocols
- Research papers and documentation
- Custom knowledge base files
- Configuration templates

#### Storage Architecture

**Security Features**:
- IAM role-based access for backend file operations
- TLS encryption for all file transfers
- Temporary credentials via AWS STS
- Regional storage with S3 bucket policies

**File Organization**:
```
s3://genascope-dev-knowledge-sources/
├── knowledge-sources/
│   ├── {account_id}/
│   │   ├── guidelines/
│   │   ├── protocols/
│   │   └── custom/
│   └── shared/
│       ├── nccn-guidelines/
│       └── public-protocols/
├── uploads/
│   └── {user_id}/
│       └── {filename}
└── configurations/
    └── {strategy_id}/
        └── exports/
```

#### Integration with Knowledge Sources

**File Upload for Knowledge Sources**:
```python
@router.post("/knowledge-sources/upload")
async def upload_knowledge_source(
    file: UploadFile = File(...),
    category: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Upload knowledge source file to S3 with proper categorization"""
    file_key = f"knowledge-sources/{current_user.account_id}/{category}/{file.filename}"
    s3_url = await storage_service.upload_file(await file.read(), file_key)
    
    # Store metadata in database
    knowledge_source = KnowledgeSource(
        name=file.filename,
        category=category,
        file_path=s3_url,
        uploaded_by=current_user.id,
        account_id=current_user.account_id
    )
    # ... save to database
```

**Security Considerations**:
- File uploads scoped to user's account
- Role-based access control for knowledge source management
- Audit logging for all file operations
- Encryption at rest and in transit
