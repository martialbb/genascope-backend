"""
Storage client service for handling file operations in the hybrid storage architecture.

This module provides abstraction for different storage backends (S3, MinIO, Local)
and handles file upload, download, and management operations.
"""
import asyncio
import hashlib
import mimetypes
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional, BinaryIO
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageType(str, Enum):
    """Enum for storage backend types"""
    S3 = "s3"
    MINIO = "minio"
    LOCAL = "local"


@dataclass
class UploadResult:
    """Result of a file upload operation"""
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
class FileValidationResult:
    """Result of file validation"""
    is_valid: bool
    error_message: Optional[str] = None
    detected_type: Optional[str] = None
    estimated_size: Optional[int] = None


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


class S3StorageClient(StorageClient):
    """AWS S3 storage client implementation with support for role assumption"""
    
    def __init__(
        self, 
        aws_access_key: Optional[str] = None, 
        aws_secret_key: Optional[str] = None, 
        region: str = "us-west-2",
        endpoint_url: Optional[str] = None,
        enable_encryption: bool = True,
        kms_key_id: Optional[str] = None,
        role_arn: Optional[str] = None,
        role_session_name: str = "genascope-backend-session",
        role_external_id: Optional[str] = None
    ):
        try:
            import boto3
            from botocore.config import Config
            
            # Configure with retry and timeout settings
            config = Config(
                region_name=region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=10
            )
            
            # Use role-based authentication if role_arn is provided
            if role_arn:
                self.s3_client = self._create_s3_client_with_role(
                    role_arn=role_arn,
                    session_name=role_session_name,
                    external_id=role_external_id,
                    region=region,
                    config=config,
                    endpoint_url=endpoint_url
                )
                logger.info(f"S3 client created with role assumption: {role_arn}")
            else:
                # Fallback to access key authentication
                if not aws_access_key or not aws_secret_key:
                    raise ValueError("Either role_arn or aws_access_key/aws_secret_key must be provided")
                
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    endpoint_url=endpoint_url,
                    config=config
                )
                logger.info("S3 client created with access key authentication")
            
            self.region = region
            self.enable_encryption = enable_encryption
            self.kms_key_id = kms_key_id
            self.role_arn = role_arn
            
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
    
    def _create_s3_client_with_role(
        self,
        role_arn: str,
        session_name: str,
        external_id: Optional[str],
        region: str,
        config,
        endpoint_url: Optional[str] = None
    ):
        """Create S3 client using STS role assumption"""
        import boto3
        
        try:
            # Create STS client with explicit regional endpoint for better reliability
            sts_endpoint = f"https://sts.{region}.amazonaws.com"
            sts_client = boto3.client('sts', 
                                    region_name=region,
                                    endpoint_url=sts_endpoint)
            
            # Prepare assume role parameters
            assume_role_params = {
                'RoleArn': role_arn,
                'RoleSessionName': session_name,
                'DurationSeconds': 3600  # 1 hour session
            }
            
            # Add external ID if provided (for cross-account access)
            if external_id:
                assume_role_params['ExternalId'] = external_id
            
            # Assume the role
            response = sts_client.assume_role(**assume_role_params)
            credentials = response['Credentials']
            
            logger.info(f"Successfully assumed role: {role_arn}")
            logger.debug(f"Session expires at: {credentials['Expiration']}")
            
            # Create S3 client with temporary credentials
            return boto3.client(
                's3',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                endpoint_url=endpoint_url,
                config=config
            )
            
        except Exception as e:
            logger.error(f"Failed to assume role {role_arn}: {str(e)}")
            raise RuntimeError(f"Role assumption failed: {str(e)}")
    
    def _refresh_credentials_if_needed(self):
        """Refresh credentials if using role assumption and they're near expiry"""
        # This is a placeholder for credential refresh logic
        # In a production environment, you might want to implement automatic refresh
        # when credentials are close to expiry
        pass
    
    async def upload_file(
        self, 
        file: BinaryIO, 
        bucket: str, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        
        # Calculate checksum
        file_content = await self._read_file_async(file)
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
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: self.s3_client.get_object(Bucket=bucket, Key=key)
            )
        return response['Body'].read()
    
    async def delete_file(self, bucket: str, key: str) -> None:
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
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    lambda: self.s3_client.head_object(Bucket=bucket, Key=key)
                )
            return True
        except Exception as e:
            if "404" in str(e):
                return False
            raise
    
    async def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
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
    
    async def _read_file_async(self, file: BinaryIO) -> bytes:
        """Read file content asynchronously"""
        if hasattr(file, 'read'):
            if asyncio.iscoroutinefunction(file.read):
                content = await file.read()
            else:
                content = file.read()
            
            # Reset file pointer if possible
            if hasattr(file, 'seek'):
                if asyncio.iscoroutinefunction(file.seek):
                    await file.seek(0)
                else:
                    file.seek(0)
        else:
            content = file
        
        return content if isinstance(content, bytes) else content.encode()


class MinIOStorageClient(StorageClient):
    """MinIO storage client implementation (S3-compatible)"""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = True,
        region: str = "us-west-2"
    ):
        try:
            from minio import Minio
            from minio.error import InvalidResponseError
            
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            self.region = region
            self.endpoint = endpoint
            self.secure = secure
            
        except ImportError:
            raise ImportError("minio is required for MinIO storage. Install with: pip install minio")
    
    async def upload_file(
        self, 
        file: BinaryIO, 
        bucket: str, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        from io import BytesIO
        
        # Calculate checksum
        file_content = await self._read_file_async(file)
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
                    len(file_content),
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
            etag=result.etag
        )
    
    async def download_file(self, bucket: str, key: str) -> bytes:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: self.client.get_object(bucket, key)
            )
        return response.read()
    
    async def delete_file(self, bucket: str, key: str) -> None:
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
        from datetime import timedelta
        
        # MinIO presigned URL
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            url = await loop.run_in_executor(
                executor,
                lambda: self.client.presigned_get_object(
                    bucket, 
                    key, 
                    expires=timedelta(seconds=expires_in)
                )
            )
        return url
    
    async def file_exists(self, bucket: str, key: str) -> bool:
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    lambda: self.client.stat_object(bucket, key)
                )
            return True
        except Exception:
            return False
    
    async def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
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
            'etag': stat.etag,
            'metadata': stat.metadata or {}
        }
    
    async def _read_file_async(self, file: BinaryIO) -> bytes:
        """Read file content asynchronously"""
        if hasattr(file, 'read'):
            if asyncio.iscoroutinefunction(file.read):
                content = await file.read()
            else:
                content = file.read()
            
            # Reset file pointer if possible
            if hasattr(file, 'seek'):
                if asyncio.iscoroutinefunction(file.seek):
                    await file.seek(0)
                else:
                    file.seek(0)
        else:
            content = file
        
        return content if isinstance(content, bytes) else content.encode()


class LocalStorageClient(StorageClient):
    """Local filesystem storage client for development/testing"""
    
    def __init__(self, base_path: str):
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
        import json
        
        # Create directory structure
        file_path = self.base_path / bucket / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        file_content = await self._read_file_async(file)
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
    
    async def _read_file_async(self, file: BinaryIO) -> bytes:
        """Read file content"""
        if hasattr(file, 'read'):
            content = file.read()
            # Reset file pointer if possible
            if hasattr(file, 'seek'):
                file.seek(0)
        else:
            content = file
        
        return content if isinstance(content, bytes) else content.encode()


def create_storage_client(config: Dict[str, Any]) -> StorageClient:
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
    elif storage_type == 'local':
        return LocalStorageClient(
            base_path=config.get('local_storage_path', './storage')
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


class FileValidator:
    """File validation utility"""
    
    def __init__(self, config: Dict[str, Any]):
        self.max_file_size = config.get('max_file_size_bytes', 100 * 1024 * 1024)  # 100MB default
        self.allowed_extensions = config.get('allowed_extensions', ['.pdf', '.docx', '.doc', '.txt', '.md'])
    
    async def validate_file(self, file, filename: str) -> FileValidationResult:
        """Comprehensive file validation"""
        try:
            # Check file extension
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                return FileValidationResult(
                    is_valid=False,
                    error_message=f"File type {file_ext} not allowed. Allowed types: {self.allowed_extensions}"
                )
            
            # Check file size
            if hasattr(file, 'size') and file.size > self.max_file_size:
                return FileValidationResult(
                    is_valid=False,
                    error_message=f"File size {file.size} exceeds limit of {self.max_file_size} bytes"
                )
            
            # Detect content type
            detected_type = mimetypes.guess_type(filename)[0]
            
            return FileValidationResult(
                is_valid=True,
                detected_type=detected_type,
                estimated_size=getattr(file, 'size', None)
            )
            
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )


def get_storage_client(storage_type: StorageType = StorageType.LOCAL, **config) -> StorageClient:
    """Factory function to get storage client based on type"""
    if storage_type == StorageType.S3:
        return S3StorageClient(**config)
    elif storage_type == StorageType.MINIO:
        return MinIOStorageClient(**config)
    elif storage_type == StorageType.LOCAL:
        return LocalStorageClient(**config)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


def get_configured_storage_client() -> StorageClient:
    """Get storage client based on environment configuration"""
    from app.core.config import settings
    
    provider = settings.STORAGE_PROVIDER.lower()
    
    if provider == "local":
        return LocalStorageClient(base_path=settings.STORAGE_BASE_PATH)
    elif provider == "s3":
        # Use role-based authentication if role ARN is provided
        if settings.AWS_ROLE_ARN:
            logger.info("Using AWS role-based authentication for S3")
            return S3StorageClient(
                region=settings.AWS_REGION,
                role_arn=settings.AWS_ROLE_ARN,
                role_session_name=settings.AWS_ROLE_SESSION_NAME,
                role_external_id=settings.AWS_ROLE_EXTERNAL_ID if settings.AWS_ROLE_EXTERNAL_ID else None
            )
        else:
            # Fallback to access key authentication
            logger.info("Using AWS access key authentication for S3")
            if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                raise ValueError("AWS credentials not configured. Set either AWS_ROLE_ARN or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY")
            
            return S3StorageClient(
                aws_access_key=settings.AWS_ACCESS_KEY_ID,
                aws_secret_key=settings.AWS_SECRET_ACCESS_KEY,
                region=settings.AWS_REGION
            )
    elif provider == "minio":
        return MinIOStorageClient(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
    elif provider == "gcp":
        # GCP client would need to be implemented
        raise NotImplementedError("GCP storage client not yet implemented")
    else:
        logger.warning(f"Unknown storage provider '{provider}', falling back to local storage")
        return LocalStorageClient(base_path=settings.STORAGE_BASE_PATH)
