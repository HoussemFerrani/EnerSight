"""
Pydantic schemas for user management
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response (no password)"""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesBase(BaseModel):
    """Base preferences schema"""
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    email_notifications: bool = True
    push_notifications: bool = True
    alert_threshold_kwh: int = 500
    date_format: str = "YYYY-MM-DD"
    currency: str = "USD"
    energy_unit: str = "kWh"


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences"""
    pass


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    alert_threshold_kwh: Optional[int] = None
    date_format: Optional[str] = None
    currency: Optional[str] = None
    energy_unit: Optional[str] = None


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for preferences response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    """Schema for password change"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
