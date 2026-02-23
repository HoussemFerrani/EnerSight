"""
Authentication Dependencies
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from backend.database.postgres import get_db
from backend.models.user import User, UserRole
from backend.utils.auth import verify_token

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session
    
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify and decode token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active - convert Column to bool
    is_active = bool(user.is_active)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Active user object
        
    Raises:
        HTTPException: 403 if user is not active
    """
    is_active = bool(current_user.is_active)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current verified user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Verified user object
        
    Raises:
        HTTPException: 403 if user is not verified
    """
    is_verified = bool(current_user.is_verified)
    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


async def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function that checks user role
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role
        if user_role != required_role and user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Admin user object
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    user_role = current_user.role
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


class OptionalAuth:
    """
    Optional authentication - returns user if authenticated, None otherwise
    Useful for endpoints that have different behavior for authenticated vs. anonymous users
    """
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """
        Get current user if authenticated, None otherwise
        
        Args:
            credentials: Optional HTTP Authorization header
            db: Database session
            
        Returns:
            Optional[User]: User object if authenticated, None otherwise
        """
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            payload = verify_token(token)
            if not payload:
                return None
            
            user_id: int = payload.get("sub")
            if user_id is None:
                return None
            
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                is_active = bool(user.is_active)
                return user if is_active else None
            return None
        except:
            return None


# Create instance for use in routes
optional_auth = OptionalAuth()
