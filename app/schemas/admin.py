"""
Pydantic schema models for administrative data transfer objects.

These schemas define the structure for request and response payloads
related to account management and administrative functions.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class SubscriptionTier(str, Enum):
    """Enumeration of possible subscription tiers"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class AccountBase(BaseModel):
    """Base model for account data"""
    name: str
    domain: str
    subscription_tier: SubscriptionTier = SubscriptionTier.STANDARD
    max_users: int = 10


class AccountCreate(AccountBase):
    """Schema for account creation requests"""
    admin_email: EmailStr
    admin_name: str
    admin_password: str
    admin_confirm_password: str
    
    @field_validator('admin_confirm_password')
    def passwords_match(cls, v, info):
        values = info.data
        if 'admin_password' in values and v != values['admin_password']:
            raise ValueError('passwords do not match')
        return v


class AccountUpdate(BaseModel):
    """Schema for account update requests"""
    name: Optional[str] = None
    domain: Optional[str] = None
    subscription_tier: Optional[SubscriptionTier] = None
    max_users: Optional[int] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    """Schema for account response data"""
    id: str
    admin_email: EmailStr
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UsageMetrics(BaseModel):
    """Schema for account usage metrics"""
    active_users: int
    total_users: int
    storage_used_mb: float
    storage_limit_mb: float
    api_calls_current_month: int
    max_api_calls: int


class AccountMetricsResponse(BaseModel):
    """Schema for account metrics response"""
    account_id: str
    account_name: str
    metrics: UsageMetrics
    last_updated: datetime


class BillingInfo(BaseModel):
    """Schema for billing information"""
    payment_method: str
    last_four: Optional[str] = None
    expiry_date: Optional[str] = None
    billing_address: Dict[str, str]
    tax_id: Optional[str] = None


class BillingUpdate(BaseModel):
    """Schema for billing information updates"""
    payment_method: Optional[str] = None
    card_number: Optional[str] = None
    expiry_date: Optional[str] = None
    cvv: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    tax_id: Optional[str] = None


class InvoiceItem(BaseModel):
    """Schema for invoice line items"""
    description: str
    quantity: int
    unit_price: float
    total: float


class Invoice(BaseModel):
    """Schema for invoice data"""
    id: str
    account_id: str
    invoice_number: str
    issue_date: date
    due_date: date
    items: List[InvoiceItem]
    subtotal: float
    tax: float
    total: float
    status: str
    paid_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)
