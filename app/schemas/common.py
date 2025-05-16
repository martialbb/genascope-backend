"""
Pydantic schema models for common data transfer objects.

These schemas define the structure for general-purpose request and response payloads
used across multiple parts of the application.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generic, TypeVar, Union
from enum import Enum


class ErrorDetail(BaseModel):
    """Schema for detailed error information"""
    loc: Optional[List[str]] = None  # Location of the error (e.g., field path)
    msg: str  # Error message
    type: str  # Error type identifier


class ErrorResponse(BaseModel):
    """Schema for API error responses"""
    detail: Union[str, List[ErrorDetail]]
    status_code: int
    error_type: Optional[str] = None


class SuccessResponse(BaseModel):
    """Schema for simple success responses"""
    message: str
    status_code: int = 200


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic schema for paginated API responses"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class SortDirection(str, Enum):
    """Enumeration of sort directions"""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Enumeration of filter operators"""
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    LT = "lt"  # Less than
    GE = "ge"  # Greater than or equal
    LE = "le"  # Less than or equal
    IN = "in"  # In a list
    NIN = "nin"  # Not in a list
    CONTAINS = "contains"  # Contains substring
    STARTS_WITH = "starts_with"  # Starts with
    ENDS_WITH = "ends_with"  # Ends with


class Filter(BaseModel):
    """Schema for filtering query parameters"""
    field: str
    operator: FilterOperator
    value: Any


class Sort(BaseModel):
    """Schema for sorting query parameters"""
    field: str
    direction: SortDirection = SortDirection.ASC


class QueryParams(BaseModel):
    """Schema for common query parameters"""
    page: int = 1
    page_size: int = 20
    sort: Optional[List[Sort]] = None
    filters: Optional[List[Filter]] = None


class HealthCheck(BaseModel):
    """Schema for API health check response"""
    status: str = "ok"
    version: str
    environment: str
    database_connected: bool
    services: Dict[str, bool]
