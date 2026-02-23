"""
Dependency Injection Container
Manages application dependencies and their lifecycles
"""

from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

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
        self._influxdb_client = None
    
    async def init_postgres(self) -> None:
        """Initialize PostgreSQL connection pool"""
        try:
            # Create async engine with connection pooling
            self._postgres_engine = create_async_engine(
                settings.postgres_url.replace("postgresql://", "postgresql+asyncpg://"),
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=settings.debug,
            )
            
            # Create session factory
            self._postgres_session_factory = async_sessionmaker(
                self._postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    async def close_postgres(self) -> None:
        """Close PostgreSQL connection pool"""
        if self._postgres_engine:
            await self._postgres_engine.dispose()
            logger.info("PostgreSQL connection pool closed")
    
    async def get_postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get PostgreSQL session (dependency)
        
        Usage:
            @app.get("/users")
            async def get_users(db: AsyncSession = Depends(get_postgres_session)):
                result = await db.execute(select(User))
                return result.scalars().all()
        """
        if not self._postgres_session_factory:
            raise RuntimeError("PostgreSQL not initialized. Call init_postgres() first.")
        
        async with self._postgres_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    def init_influxdb(self) -> None:
        """Initialize InfluxDB client"""
        try:
            self._influxdb_client = InfluxDBClientAsync(
                url=settings.influxdb_url,
                token=settings.influxdb_token,
                org=settings.influxdb_org,
                timeout=settings.influxdb_timeout,
            )
            logger.info("InfluxDB client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            raise
    
    async def close_influxdb(self) -> None:
        """Close InfluxDB client"""
        if self._influxdb_client:
            await self._influxdb_client.close()
            logger.info("InfluxDB client closed")
    
    def get_influxdb_client(self) -> InfluxDBClientAsync:
        """
        Get InfluxDB client (dependency)
        
        Usage:
            @app.get("/energy")
            async def get_energy(influx: InfluxDBClientAsync = Depends(get_influxdb_client)):
                query_api = influx.query_api()
                ...
        """
        if not self._influxdb_client:
            raise RuntimeError("InfluxDB not initialized. Call init_influxdb() first.")
        return self._influxdb_client


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


def get_influxdb_client() -> InfluxDBClientAsync:
    """FastAPI dependency for InfluxDB client"""
    db_manager = get_database_manager()
    return db_manager.get_influxdb_client()


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

def get_energy_service() -> EnergyService:
    """
    Get EnergyService instance with all dependencies
    
    FastAPI Dependency for injecting EnergyService into route handlers.
    Creates service with repository and ML models.
    
    Usage:
        @router.post("/predict")
        async def predict(service: EnergyService = Depends(get_energy_service)):
            result = await service.predict_consumption(...)
            return result
    """
    from backend.repositories.energy_repository import EnergyDataRepository
    
    # Get database client
    db_manager = get_database_manager()
    
    # Create repository (may be with mock client if InfluxDB not configured)
    repository = None
    try:
        influx_client = db_manager.get_influxdb_client()
        bucket = settings.influxdb_bucket
        org = settings.influxdb_org
        repository = EnergyDataRepository(
            influxdb_client=influx_client,
            bucket=bucket,
            org=org,
        )
    except RuntimeError:
        # InfluxDB not configured - use defaults
        logger.warning("InfluxDB not available, some features may be limited")
    
    # Get ML models from registry (optional - may not be loaded)
    model_registry = get_model_registry()
    
    try:
        regression_model = model_registry.get_model("regression")
    except (ValueError, Exception):
        regression_model = None
        logger.warning("Regression model not loaded")
    
    try:
        lstm_model = model_registry.get_model("lstm")
    except (ValueError, Exception):
        lstm_model = None
        logger.warning("LSTM model not loaded")
    
    try:
        anomaly_detector = model_registry.get_model("anomaly_detector")
    except (ValueError, Exception):
        anomaly_detector = None
        logger.warning("Anomaly detector not loaded")
    
    # Create and return service
    if repository is None:
        logger.warning("No energy repository available, EnergyService will have limited functionality")
    
    return EnergyService(
        energy_repository=repository,
        regression_model=regression_model,
        lstm_model=lstm_model,
        anomaly_detector=anomaly_detector,
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
        # PostgreSQL (optional - may not be configured)
        if settings.postgres_password:
            await db_manager.init_postgres()
        else:
            logger.warning("PostgreSQL credentials not configured, skipping initialization")
    except Exception as e:
        logger.warning(f"PostgreSQL initialization failed: {e}")
    
    try:
        # InfluxDB (optional - may not be configured)
        if settings.influxdb_token:
            db_manager.init_influxdb()
        else:
            logger.warning("InfluxDB token not configured, skipping initialization")
    except Exception as e:
        logger.warning(f"InfluxDB initialization failed: {e}")
    
    # Register ML models
    logger.info("Registering ML models...")
    model_registry = get_model_registry()
    
    try:
        from backend.ml.model_loaders import (
            load_regression_model,
            load_lstm_model,
            load_anomaly_detector,
        )
        
        # Register regression model (Random Forest)
        model_registry.register_model(
            "regression",
            lambda: load_regression_model("random_forest")
        )
        logger.info("Registered regression model (Random Forest)")
        
        # Register LSTM model
        model_registry.register_model(
            "lstm",
            load_lstm_model
        )
        logger.info("Registered LSTM model")
        
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
    
    # Close database connections
    await db_manager.close_postgres()
    await db_manager.close_influxdb()
    
    logger.info("Application dependencies cleaned up")
