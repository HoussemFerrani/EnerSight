"""
Repository Pattern - Base Classes
Provides abstraction layer for data access with generic CRUD operations
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Generic type for model
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Abstract base repository with generic CRUD operations
    Implements Repository Pattern for data access abstraction
    
    Benefits:
    - Decouples business logic from data access
    - Enables easy testing with mock repositories
    - Centralizes query logic
    - Provides consistent interface across entities
    """
    
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        """
        Initialize repository
        
        Args:
            session: SQLAlchemy async session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model
    
    async def create(self, data: CreateSchemaType) -> ModelType:
        """
        Create new entity
        
        Args:
            data: Pydantic schema with creation data
        
        Returns:
            Created model instance
        """
        db_obj = self.model(**data.model_dump())
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get entity by ID
        
        Args:
            id: Entity identifier
        
        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get all entities with optional filtering and pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field:value filters
        
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, id: Any, data: UpdateSchemaType) -> Optional[ModelType]:
        """
        Update entity
        
        Args:
            id: Entity identifier
            data: Pydantic schema with update data
        
        Returns:
            Updated model instance or None if not found
        """
        # Get existing entity
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: Any) -> bool:
        """
        Delete entity
        
        Args:
            id: Entity identifier
        
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Count entities with optional filtering
        
        Args:
            filters: Dictionary of field:value filters
        
        Returns:
            Number of matching entities
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return len(list(result.scalars().all()))
    
    async def exists(self, id: Any) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity identifier
        
        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None


class UnitOfWork(ABC):
    """
    Unit of Work Pattern
    Manages transactions across multiple repositories
    
    Benefits:
    - Ensures atomicity across multiple operations
    - Centralizes transaction management
    - Prevents partial updates on failures
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self):
        """Enter async context manager"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager"""
        if exc_type:
            # Rollback on exception
            await self.rollback()
        else:
            # Commit on success
            await self.commit()
    
    async def commit(self) -> None:
        """Commit transaction"""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback transaction"""
        await self.session.rollback()
    
    @abstractmethod
    def get_repository(self, repository_class: type) -> Any:
        """
        Get repository instance
        
        Args:
            repository_class: Repository class
        
        Returns:
            Repository instance
        """
        pass
