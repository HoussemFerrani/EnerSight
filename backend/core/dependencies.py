"""
Dependency Injection Container
Manages application dependencies and their lifecycles
"""

from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.services.energy_service import EnergyService

logger = get_logger(__name__)
settings = get_settings()


# ==================== Database Dependencies ====================

class DatabaseManager:
    """
    Manages database connections and sessions
    Implements connection pooling and lifecycle management
    """
    
    def __init__(self):
        self._postgres_engine = None
        self._postgres_session_factory = None

    async def init_postgres(self) -> None:
        """Initialize Supabase Postgres async engine and session factory."""
        try:
            url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            # Supabase's transaction pooler (pgbouncer) does NOT support prepared statements.
            # asyncpg caches them by default — disable the cache and prepared-statement
            # creation to avoid "prepared statement does not exist" errors.
            self._postgres_engine = create_async_engine(
                url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_pre_ping=True,
                echo=settings.debug,
                connect_args={
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                },
            )
            self._postgres_session_factory = async_sessionmaker(
                self._postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            logger.info("Postgres async engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Postgres: {e}")
            raise

    async def close_postgres(self) -> None:
        if self._postgres_engine:
            await self._postgres_engine.dispose()
            logger.info("Postgres engine disposed")

    async def get_postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._postgres_session_factory:
            raise RuntimeError("Postgres not initialized. Call init_postgres() first.")
        async with self._postgres_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Singleton instance
@lru_cache()
def get_database_manager() -> DatabaseManager:
    """Get database manager singleton"""
    return DatabaseManager()


# Convenience functions for FastAPI dependencies
async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for PostgreSQL session"""
    db_manager = get_database_manager()
    async for session in db_manager.get_postgres_session():
        yield session


# ==================== Service Dependencies ====================

class ServiceContainer:
    """
    Service container for dependency injection
    Manages service instances and their dependencies
    """
    
    def __init__(self):
        self._services = {}
    
    def register(self, service_name: str, service_factory):
        """
        Register a service factory
        
        Args:
            service_name: Unique service identifier
            service_factory: Callable that creates service instance
        """
        self._services[service_name] = service_factory
        logger.debug(f"Service registered: {service_name}")
    
    def get(self, service_name: str):
        """
        Get service instance
        
        Args:
            service_name: Service identifier
        
        Returns:
            Service instance
        """
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not registered")
        
        factory = self._services[service_name]
        return factory()
    
    def has(self, service_name: str) -> bool:
        """Check if service is registered"""
        return service_name in self._services


@lru_cache()
def get_service_container() -> ServiceContainer:
    """Get service container singleton"""
    return ServiceContainer()


# ==================== ML Model Dependencies ====================

class ModelRegistry:
    """
    Registry for ML models
    Implements lazy loading and caching
    """
    
    def __init__(self):
        self._models = {}
    
    def register_model(self, model_name: str, model_loader):
        """
        Register a model loader
        
        Args:
            model_name: Unique model identifier
            model_loader: Callable that loads the model
        """
        self._models[model_name] = {
            "loader": model_loader,
            "instance": None,
            "loaded": False,
        }
        logger.debug(f"Model registered: {model_name}")
    
    def get_model(self, model_name: str):
        """
        Get model instance (lazy loaded)
        
        Args:
            model_name: Model identifier
        
        Returns:
            Model instance
        """
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not registered")
        
        model_info = self._models[model_name]
        
        # Lazy load on first access
        if not model_info["loaded"]:
            logger.info(f"Loading model: {model_name}")
            model_info["instance"] = model_info["loader"]()
            model_info["loaded"] = True
        
        return model_info["instance"]
    
    def unload_model(self, model_name: str) -> None:
        """Unload model from memory"""
        if model_name in self._models:
            self._models[model_name]["instance"] = None
            self._models[model_name]["loaded"] = False
            logger.info(f"Model unloaded: {model_name}")


@lru_cache()
def get_model_registry() -> ModelRegistry:
    """Get model registry singleton"""
    return ModelRegistry()


# ==================== Service Layer Dependencies ====================

async def get_energy_service(
    session: AsyncSession = Depends(get_postgres_session),
) -> EnergyService:
    """
    Construct an EnergyService bound to a Postgres session and the ML registry.

    FastAPI resolves the session via `Depends(get_postgres_session)`.
    """
    from backend.repositories.energy_repository import EnergyDataRepository
    from backend.repositories.prediction_log_repository import PredictionLogRepository

    repository = EnergyDataRepository(session=session)
    prediction_log_repository = PredictionLogRepository(session=session)

    model_registry = get_model_registry()
    try:
        regression_model = model_registry.get_model("regression")
    except Exception:
        regression_model = None
        logger.warning("Regression model not loaded")
    try:
        lstm_model = model_registry.get_model("lstm")
    except Exception:
        lstm_model = None
        logger.warning("LSTM model not loaded")
    try:
        lstm_estimator = model_registry.get_model("lstm_estimator")
    except Exception:
        lstm_estimator = None
        logger.warning("Multivariate LSTM estimator not loaded")
    try:
        anomaly_detector = model_registry.get_model("anomaly_detector")
    except Exception:
        anomaly_detector = None
        logger.warning("Anomaly detector not loaded")

    return EnergyService(
        energy_repository=repository,
        regression_model=regression_model,
        lstm_model=lstm_model,
        lstm_estimator=lstm_estimator,
        anomaly_detector=anomaly_detector,
        prediction_log_repository=prediction_log_repository,
    )


# ==================== Lifespan Management ====================

async def init_dependencies() -> None:
    """
    Initialize all application dependencies
    Called on application startup
    """
    logger.info("Initializing application dependencies...")
    
    # Initialize databases
    db_manager = get_database_manager()
    
    try:
        if settings.database_url:
            await db_manager.init_postgres()
        else:
            logger.warning("DATABASE_URL not configured, skipping Postgres initialization")
    except Exception as e:
        logger.warning(f"Postgres initialization failed: {e}")


    # Register ML models
    logger.info("Registering ML models...")
    model_registry = get_model_registry()
    
    try:
        from backend.ml.model_loaders import (
            load_regression_model,
            load_lstm_model,
            load_lstm_multivariate,
            load_anomaly_detector,
        )
        
        # Register regression model (Random Forest)
        model_registry.register_model(
            "regression",
            lambda: load_regression_model("random_forest")
        )
        logger.info("Registered regression model (Random Forest)")
        
        # Register LSTM model (univariate forecaster — legacy /forecast path)
        model_registry.register_model(
            "lstm",
            load_lstm_model
        )
        logger.info("Registered LSTM model")

        # Register multivariate LSTM estimator (powers /predict?model=lstm)
        model_registry.register_model(
            "lstm_estimator",
            load_lstm_multivariate
        )
        logger.info("Registered multivariate LSTM estimator")
        
        # Register anomaly detector
        model_registry.register_model(
            "anomaly_detector",
            load_anomaly_detector
        )
        logger.info("Registered anomaly detector")
        
        logger.info("ML models registered successfully")
    except Exception as e:
        logger.error(f"Failed to register ML models: {e}")
        logger.warning("ML prediction features will not be available")
    
    logger.info("Application dependencies initialized")


async def cleanup_dependencies() -> None:
    """
    Cleanup all application dependencies
    Called on application shutdown
    """
    logger.info("Cleaning up application dependencies...")
    
    db_manager = get_database_manager()
    
    await db_manager.close_postgres()
    
    logger.info("Application dependencies cleaned up")
