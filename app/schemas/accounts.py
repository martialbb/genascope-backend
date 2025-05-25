from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class AccountBase(BaseModel):
    """Base schema for account data"""
    name: str = Field(..., description="Account name")
    domain: str = Field(..., description="Account domain")

class AccountCreate(AccountBase):
    """Schema for creating new accounts"""
    admin_email: EmailStr = Field(..., description="Email for the account admin")
    admin_name: str = Field(..., description="Name for the account admin")
    admin_password: str = Field(..., min_length=8, description="Password for the account admin")
    admin_confirm_password: str = Field(..., min_length=8, description="Confirm password for the account admin")

    def validate_passwords_match(self):
        """Validate that password and confirm_password match"""
        if self.admin_password != self.admin_confirm_password:
            return False
        return True

class AccountUpdate(BaseModel):
    """Schema for updating existing accounts"""
    name: Optional[str] = Field(None, description="Account name")
    domain: Optional[str] = Field(None, description="Account domain")
    is_active: Optional[bool] = Field(None, description="Whether the account is active")

    model_config = ConfigDict(from_attributes=True)

class AccountResponse(BaseModel):
    """Schema for account responses"""
    id: str = Field(..., description="Account ID")
    name: str = Field(..., description="Account name")
    domain: str = Field(..., description="Account domain")
    is_active: bool = Field(..., description="Whether the account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
