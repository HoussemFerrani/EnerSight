"""
FastAPI auth dependencies — Supabase-aware.

Flow:
1. Frontend hits FastAPI with `Authorization: Bearer <supabase_access_token>`.
2. `verify_token` decodes the JWT locally using the project JWT secret.
3. We look up `public.profiles` by the `sub` claim (Supabase user UUID).
4. Routes receive a `Profile` (aliased as `User` for backwards compatibility).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database.postgres import get_db
from backend.models.user import Profile as User
from backend.utils.auth import verify_token

security = HTTPBearer()


def _resolve_uuid(payload: dict) -> Optional[UUID]:
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        return UUID(str(sub))
    except (ValueError, TypeError):
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_uuid = _resolve_uuid(payload)
    if user_uuid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        # Trigger should have created the profile, but handle the race anyway.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Profile not found for this user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not bool(user.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    user.last_login = datetime.utcnow()
    db.commit()
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not bool(current_user.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


async def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not bool(current_user.is_verified):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return current_user


def require_role(required_role: str):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role = str(current_user.role or "user")
        if role != required_role and role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}",
            )
        return current_user
    return role_checker


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if str(current_user.role or "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


class OptionalAuth:
    """Returns the Profile if authenticated, None otherwise."""

    def __init__(self):
        self.security = HTTPBearer(auto_error=False)

    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
        db: Session = Depends(get_db),
    ) -> Optional[User]:
        if not credentials:
            return None
        payload = verify_token(credentials.credentials)
        if not payload:
            return None
        user_uuid = _resolve_uuid(payload)
        if not user_uuid:
            return None
        user = db.query(User).filter(User.id == user_uuid).first()
        if user and bool(user.is_active):
            return user
        return None


optional_auth = OptionalAuth()
