"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend.database.postgres import get_db
from backend.models.user import User, UserPreferences, UserRole
from backend.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    UserPreferencesCreate, UserPreferencesUpdate, UserPreferencesResponse,
    PasswordChange
)
from backend.utils.auth import get_password_hash, verify_password

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user.email.lower()) | (User.username == user.username)
    ).first()
    
    if existing_user:
        if existing_user.email.lower() == user.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        address=user.address,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default preferences
    preferences = UserPreferences(user_id=db_user.id)
    db.add(preferences)
    db.commit()
    
    return db_user


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all users (paginated)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/users/username/{username}", response_model=UserResponse)
async def get_user_by_username(username: str, db: Session = Depends(get_db)):
    """Get a user by username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete preferences first
    db.query(UserPreferences).filter(UserPreferences.user_id == user_id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return None


@router.post("/users/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_data: PasswordChange,
    db: Session = Depends(get_db)
):
    """Change user password"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not verify_password(password_data.old_password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/users/{user_id}/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    """Get user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
    
    return preferences


@router.put("/users/{user_id}/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: int,
    preferences_update: UserPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        # Create preferences if they don't exist
        preferences = UserPreferences(user_id=user_id)
        db.add(preferences)
    
    # Update fields
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences)
    
    return preferences


@router.get("/users/stats/summary")
async def get_user_stats(db: Session = Depends(get_db)):
    """Get user statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    # Count by role
    admins = db.query(User).filter(User.role == UserRole.ADMIN).count()
    regular_users = db.query(User).filter(User.role == UserRole.USER).count()
    viewers = db.query(User).filter(User.role == UserRole.VIEWER).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "by_role": {
            "admins": admins,
            "users": regular_users,
            "viewers": viewers
        }
    }
