"""
FastAPI Main Application - Clean Architecture
Entry point for the EnerSight API server

Implements:
- Clean Architecture principles
- Dependency Injection
- Structured logging
- Global error handling
- Configuration management
- Lifespan management
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.config import get_settings
from backend.core.logging import setup_logging, get_logger
from backend.core.error_handlers import register_exception_handlers
from backend.core.dependencies import init_dependencies, cleanup_dependencies

# Load settings
settings = get_settings()

# Configure logging
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    use_json=settings.is_production,
    use_colors=settings.is_development,
)

logger = get_logger(__name__)


# ==================== Security Middleware ====================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server header for security
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting EnerSight API v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("=" * 60)
    
    # Store background tasks
    background_tasks = []
    
    try:
        # Initialize dependencies (databases, services, etc.)
        await init_dependencies()
        
        # Initialize PostgreSQL database
        try:
            from backend.database.postgres import init_db
            init_db()
            logger.info("✓ PostgreSQL database initialized")
        except Exception as db_error:
            logger.warning(f"⚠ PostgreSQL initialization skipped: {db_error}")
        
        # Start alert monitoring service
        try:
            from backend.services.alert_monitor import alert_monitor
            import asyncio
            monitor_task = asyncio.create_task(alert_monitor.start())
            background_tasks.append(monitor_task)
            logger.info("✓ Alert monitoring service started")
        except Exception as alert_error:
            logger.warning(f"⚠ Alert monitoring service failed to start: {alert_error}")
        
        logger.info("✓ Application started successfully")
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        # Stop alert monitoring
        from backend.services.alert_monitor import alert_monitor
        alert_monitor.stop()
        
        # Cancel background tasks
        for task in background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        await cleanup_dependencies()
        logger.info("✓ Application shut down cleanly")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered platform for real-time energy monitoring, predictive analytics, and optimization",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    openapi_url="/api/openapi.json",
    debug=settings.debug,
)


# ==================== Middleware Configuration ====================

# CORS - Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host (production only)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.enersight.com", "localhost"]
    )


# ==================== Exception Handlers ====================

register_exception_handlers(app)


# ==================== API Routes ====================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "operational",
        "documentation": "/api/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    Returns detailed status of all system components
    """
    from backend.core.dependencies import get_database_manager
    
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "components": {
            "api": "operational",
        }
    }
    
    try:
        db_manager = get_database_manager()
        if db_manager._postgres_engine:
            health_status["components"]["postgres"] = "connected"
        else:
            health_status["components"]["postgres"] = "not_configured"
    except Exception as e:
        logger.warning(f"Health check warning: {e}")
        health_status["components"]["database"] = "unavailable"
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/api/v1/info", tags=["Info"])
async def api_info():
    """
    API information and capabilities
    """
    return {
        "api_version": "v1",
        "features": [
            "Real-time energy monitoring",
            "ML-based consumption prediction",
            "Anomaly detection",
            "Historical data analysis",
            "IoT sensor integration",
        ],
        "ml_models": {
            "regression": ["Random Forest", "Gradient Boosting"],
            "time_series": ["LSTM"],
            "anomaly_detection": ["Isolation Forest"],
        },
        "endpoints": {
            "energy": "/api/v1/energy",
            "predictions": "/api/v1/predictions",
            "anomalies": "/api/v1/anomalies",
        }
    }


# ==================== API Routers ====================

from backend.api.routes import energy, predictions, anomalies
from backend.api.v1 import websocket, users, auth, alerts, analytics_enhanced, optimizations, reports

app.include_router(
    energy.router,
    prefix="/api/v1/energy",
    tags=["Energy Data"]
)

app.include_router(
    predictions.router,
    prefix="/api/v1/predictions",
    tags=["Predictions"]
)

app.include_router(
    anomalies.router,
    prefix="/api/v1/anomalies",
    tags=["Anomalies"]
)

# WebSocket for real-time data streaming
app.include_router(
    websocket.router,
    prefix="/api/v1",
    tags=["Real-time Data"]
)

# Authentication endpoints
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

# User management endpoints
app.include_router(
    users.router,
    prefix="/api/v1",
    tags=["User Management"]
)

# Alert endpoints
app.include_router(
    alerts.router,
    prefix="/api/v1/alerts",
    tags=["Alerts"]
)

# Enhanced analytics endpoints
app.include_router(
    analytics_enhanced.router,
    prefix="/api/v1/analytics",
    tags=["Enhanced Analytics"]
)

# Optimization recommendations
app.include_router(
    optimizations.router,
    prefix="/api/v1/optimizations",
    tags=["Optimizations"]
)

# Reports (PDF + CSV)
app.include_router(
    reports.router,
    prefix="/api/v1/reports",
    tags=["Reports"]
)


# ==================== Application Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Uvicorn server on {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=settings.debug,
    )
