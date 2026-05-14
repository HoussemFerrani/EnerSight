"""
Auth routes.

Authentication itself (login, signup, password reset, refresh) is now handled
client-side by Supabase Auth. The backend only:
 - verifies the incoming JWT (see `get_current_user`)
 - exposes profile/session info derived from the verified token

The /login, /logout, /refresh endpoints from the previous implementation have
been removed — the frontend now calls Supabase directly for those.
"""
from fastapi import APIRouter, Depends

from backend.api.dependencies.auth import get_current_user
from backend.core.logging import get_logger
from backend.models.user import Profile as User
from backend.schemas.auth import CurrentUserResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=CurrentUserResponse, summary="Get current user profile")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the authenticated user."""
    return CurrentUserResponse.model_validate(current_user)


@router.get("/verify", summary="Verify Supabase access token")
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """Returns 200 with basic claims if the token verifies; 401 otherwise."""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/session", summary="Get session info")
async def get_session(current_user: User = Depends(get_current_user)):
    """Profile + activity info for the current session."""
    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
        "is_active": bool(current_user.is_active),
        "is_verified": bool(current_user.is_verified),
        "last_login": current_user.last_login,
        "created_at": current_user.created_at,
    }
