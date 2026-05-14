"""
User profile and preferences endpoints (Supabase-backed).

Account lifecycle (signup, password change, deletion, email verification) is
owned by Supabase Auth and called directly from the frontend or via the
service-role admin API. The endpoints below operate on `public.profiles` and
`public.user_preferences`, scoped to the authenticated caller.
"""
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies.auth import get_current_user, require_admin
from backend.database.postgres import get_db
from backend.models.user import Profile as User
from backend.models.user import UserPreferences
from backend.schemas.user import (
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id (must be a UUID)")


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: list profiles."""
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a profile by UUID. Non-admins can only fetch their own."""
    uid = _parse_uuid(user_id)
    if uid != current_user.id and str(current_user.role) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users/username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile fields. Role changes require admin."""
    uid = _parse_uuid(user_id)
    is_self = uid == current_user.id
    is_admin = str(current_user.role) == "admin"
    if not (is_self or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    if "role" in update_data and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can change roles")
    # Email is owned by auth.users; reject changes here.
    update_data.pop("email", None)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = _parse_uuid(user_id)
    if uid != current_user.id and str(current_user.role) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == uid).first()
    if not prefs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preferences not found")
    return prefs


@router.put("/users/{user_id}/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: str,
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = _parse_uuid(user_id)
    if uid != current_user.id and str(current_user.role) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == uid).first()
    if not prefs:
        prefs = UserPreferences(user_id=uid)
        db.add(prefs)

    for field, value in preferences_update.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/users/stats/summary")
async def get_user_stats(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active.is_(True)).count()
    verified = db.query(User).filter(User.is_verified.is_(True)).count()
    admins = db.query(User).filter(User.role == "admin").count()
    regular = db.query(User).filter(User.role == "user").count()
    viewers = db.query(User).filter(User.role == "viewer").count()
    return {
        "total_users": total,
        "active_users": active,
        "verified_users": verified,
        "by_role": {"admins": admins, "users": regular, "viewers": viewers},
    }
