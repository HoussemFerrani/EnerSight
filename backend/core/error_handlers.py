"""
Global Exception Handler Middleware
Centralizes error handling with proper HTTP status codes and response formatting
"""

import traceback
from typing import Any, Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.exceptions import (
    EnerSightException,
    APIException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    RateLimitExceededError,
    DatabaseException,
    MLException,
    IoTException,
)
from backend.core.logging import get_logger

logger = get_logger(__name__)


async def enersight_exception_handler(request: Request, exc: EnerSightException) -> JSONResponse:
    """
    Handle custom EnerSight exceptions
    Maps exception types to appropriate HTTP status codes
    """
    
    # Map exception types to status codes
    status_code_map = {
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
        ResourceAlreadyExistsError: status.HTTP_409_CONFLICT,
        RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
        DatabaseException: status.HTTP_503_SERVICE_UNAVAILABLE,
        MLException: status.HTTP_500_INTERNAL_SERVER_ERROR,
        IoTException: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    
    # Determine status code
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    for exc_type, code in status_code_map.items():
        if isinstance(exc, exc_type):
            status_code = code
            break
    
    # Log the error
    logger.error(
        f"EnerSight exception: {exc.code}",
        extra={
            "exception_type": type(exc).__name__,
            "error_code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # Build response
    response_data: dict[str, Any] = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "type": type(exc).__name__,
        }
    }
    
    # Include details if available (exclude in production for security)
    if exc.details:
        response_data["error"]["details"] = exc.details
    
    return JSONResponse(
        status_code=status_code,
        content=response_data,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI validation errors (Pydantic)
    Returns clean error messages with field details
    """
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        "Validation error",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "type": "ValidationError",
                "details": {
                    "errors": errors,
                }
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle standard HTTP exceptions
    Provides consistent error response format
    """
    
    logger.info(
        f"HTTP exception: {exc.status_code}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "type": "HTTPException",
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions
    Logs full traceback and returns generic error message
    """
    
    # Log full traceback for debugging
    logger.critical(
        "Unhandled exception",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )
    
    # Don't expose internal errors to clients
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "type": "InternalServerError",
            }
        },
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(EnerSightException, enersight_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    
    logger.info("Exception handlers registered successfully")
