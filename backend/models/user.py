"""
Profile and user preference ORM models, mirroring the Supabase schema.

Authentication is owned by Supabase Auth — `auth.users` is the source of truth
for credentials, sessions, and email verification. `public.profiles` holds
application-specific data and is keyed by the same UUID.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from backend.database.postgres import Base


class Profile(Base):
    """Application profile keyed by auth.users(id)."""
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    phone = Column(String)
    address = Column(Text)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Profile {self.username} ({self.id})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "phone": self.phone,
            "address": self.address,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Backwards-compat alias: existing code paths import `User` from this module.
User = Profile


class UserPreferences(Base):
    """User-scoped UI/notification preferences."""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    theme = Column(String, default="light")
    language = Column(String, default="en")
    timezone = Column(String, default="UTC")
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    alert_threshold_kwh = Column(Integer, default=500)
    date_format = Column(String, default="YYYY-MM-DD")
    currency = Column(String, default="USD")
    energy_unit = Column(String, default="kWh")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserPreferences user_id={self.user_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "theme": self.theme,
            "language": self.language,
            "timezone": self.timezone,
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "alert_threshold_kwh": self.alert_threshold_kwh,
            "date_format": self.date_format,
            "currency": self.currency,
            "energy_unit": self.energy_unit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
