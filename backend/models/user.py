"""
Database models for user management
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from backend.database.postgres import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile fields
    phone = Column(String(20))
    address = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value if self.role is not None else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "phone": self.phone,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
            "last_login": self.last_login.isoformat() if self.last_login is not None else None,
        }


class UserPreferences(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Dashboard preferences
    theme = Column(String(20), default="light")  # light, dark, auto
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    alert_threshold_kwh = Column(Integer, default=500)
    
    # Display preferences
    date_format = Column(String(20), default="YYYY-MM-DD")
    currency = Column(String(10), default="USD")
    energy_unit = Column(String(10), default="kWh")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserPreferences user_id={self.user_id}>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "theme": self.theme,
            "language": self.language,
            "timezone": self.timezone,
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "alert_threshold_kwh": self.alert_threshold_kwh,
            "date_format": self.date_format,
            "currency": self.currency,
            "energy_unit": self.energy_unit,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }
