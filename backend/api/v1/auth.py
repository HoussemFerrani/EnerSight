"""
Authentication Routes
Endpoints for user authentication and session management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from backend.database.postgres import get_db
from backend.models.user import User
from backend.schemas.auth import (
    LoginRequest,
    TokenResponse,
    LogoutResponse,
    CurrentUserResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from backend.utils.auth import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from backend.api.dependencies.auth import get_current_user, get_current_active_user
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticate user and return JWT access token"
)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with username/email and password
    
    Returns:
    - JWT access token
    - User information
    - Token expiration time
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    
    if not user:
        logger.warning(f"Login attempt failed: user not found - {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password - convert SQLAlchemy Column to Python string
    hashed_pass = str(user.hashed_password)
    if not verify_password(credentials.password, hashed_pass):
        logger.warning(f"Login attempt failed: incorrect password - {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active - convert Column to bool
    is_active = bool(user.is_active)
    if not is_active:
        logger.warning(f"Login attempt failed: inactive user - {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token - convert SQLAlchemy objects to Python values
    user_id_val = int(user.id)
    username_val = str(user.username)
    role_val = str(user.role.value) if user.role else "user"
    email_val = str(user.email)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id_val, "username": username_val, "role": role_val},
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"User logged in successfully: {username_val} (ID: {user_id_val})")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user_id=user_id_val,
        username=username_val,
        email=email_val
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User Logout",
    description="Logout current user (client should discard token)"
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user
    
    Note: Since we're using JWT tokens, actual logout happens on the client side
    by discarding the token. This endpoint is mainly for logging purposes.
    
    In a production system, you might want to implement a token blacklist.
    """
    logger.info(f"User logged out: {current_user.username} (ID: {current_user.id})")
    
    return LogoutResponse(
        message="Successfully logged out",
        logged_out_at=datetime.utcnow()
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get Current User",
    description="Get information about the currently authenticated user"
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Returns detailed information about the authenticated user,
    including profile data and account status.
    """
    return CurrentUserResponse.model_validate(current_user)


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh Access Token",
    description="Get a new access token using refresh token (simplified version)"
)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh access token
    
    Note: This is a simplified version that creates a new token for the current user.
    In a production system, you'd implement proper refresh token rotation.
    """
    # Check if user is still active - convert Column to bool
    is_active = bool(current_user.is_active)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create new access token - convert SQLAlchemy objects to Python values
    user_id_val = int(current_user.id)
    username_val = str(current_user.username)
    role_val = str(current_user.role.value) if current_user.role else "user"
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id_val, "username": username_val, "role": role_val},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Token refreshed for user: {username_val} (ID: {user_id_val})")
    
    return TokenRefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get(
    "/verify",
    summary="Verify Token",
    description="Verify if the current authentication token is valid"
)
async def verify_token_endpoint(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if token is valid
    
    Returns basic user info if token is valid,
    otherwise returns 401 error.
    """
    return {
        "valid": True,
        "user_id": int(current_user.id),
        "username": str(current_user.username),
        "email": str(current_user.email),
        "role": str(current_user.role.value) if current_user.role else "user"
    }


@router.get(
    "/session",
    summary="Get Session Info",
    description="Get current session information"
)
async def get_session(
    current_user: User = Depends(get_current_user)
):
    """
    Get session information
    
    Returns information about the current authentication session,
    useful for debugging and monitoring.
    """
    return {
        "user_id": int(current_user.id),
        "username": str(current_user.username),
        "email": str(current_user.email),
        "role": str(current_user.role.value) if current_user.role else "user",
        "is_active": bool(current_user.is_active),
        "is_verified": bool(current_user.is_verified),
        "last_login": current_user.last_login,
        "created_at": current_user.created_at
    }
