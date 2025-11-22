"""CRUD operations for User model."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base import CRUDBase
from app.database.models.user import User


class CRUDUser(CRUDBase[User]):
    """CRUD operations for User model."""

    async def get_by_phone(self, db: AsyncSession, phone_number: str) -> User | None:
        """Get a user by phone number.

        Args:
            db: Database session
            phone_number: User's phone number

        Returns:
            User instance or None if not found
        """
        result = await db.execute(select(User).where(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> list[User]:
        """Get users by name (partial match).

        Args:
            db: Database session
            name: User's name (partial match)

        Returns:
            List of User instances
        """
        result = await db.execute(select(User).where(User.name.ilike(f"%{name}%")))
        return list(result.scalars().all())


# Create instance
user_crud = CRUDUser(User)

