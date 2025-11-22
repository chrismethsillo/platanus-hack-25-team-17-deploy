"""Base CRUD operations for SQLAlchemy models.

Provides generic CRUD operations that can be inherited and extended
for specific models.
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """Base class for CRUD operations.

    Args:
        model: SQLAlchemy model class

    Example:
        ```python
        from app.database.models import User
        from app.database.crud.base import CRUDBase

        class CRUDUser(CRUDBase[User]):
            async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
                result = await db.execute(select(User).where(User.email == email))
                return result.scalar_one_or_none()

        user_crud = CRUDUser(User)
        ```
    """

    def __init__(self, model: type[ModelType]) -> None:
        """Initialize CRUD object with a SQLAlchemy model.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Get a single record by ID.

        Args:
            db: Database session
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Get multiple records with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: dict[str, Any]) -> ModelType:
        """Create a new record.

        Args:
            db: Database session
            obj_in: Dictionary with model data

        Returns:
            Created model instance
        """
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception:
            await db.rollback()
            raise

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict[str, Any]
    ) -> ModelType:
        """Update an existing record.

        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Dictionary with updated data

        Returns:
            Updated model instance
        """
        try:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception:
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, *, id: Any) -> ModelType | None:
        """Delete a record by ID.

        Args:
            db: Database session
            id: Primary key value

        Returns:
            Deleted model instance or None if not found
        """
        obj = await self.get(db, id=id)
        if obj:
            try:
                await db.delete(obj)
                await db.commit()
            except Exception:
                await db.rollback()
                raise
        return obj
