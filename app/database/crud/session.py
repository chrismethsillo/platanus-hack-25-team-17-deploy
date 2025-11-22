"""CRUD operations for Session model."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base import CRUDBase
from app.database.models.session import Session, SessionStatus


class CRUDSession(CRUDBase[Session]):
    """CRUD operations for Session model."""

    async def get_by_owner(self, db: AsyncSession, owner_id: int) -> list[Session]:
        """Get sessions by owner ID.

        Args:
            db: Database session
            owner_id: Owner's user ID

        Returns:
            List of Session instances
        """
        result = await db.execute(select(Session).where(Session.owner_id == owner_id))
        return list(result.scalars().all())

    async def get_by_status(self, db: AsyncSession, status: SessionStatus) -> list[Session]:
        """Get sessions by status.

        Args:
            db: Database session
            status: Session status

        Returns:
            List of Session instances
        """
        result = await db.execute(select(Session).where(Session.status == status))
        return list(result.scalars().all())

    async def get_active_sessions(self, db: AsyncSession) -> list[Session]:
        """Get all active sessions.

        Args:
            db: Database session

        Returns:
            List of active Session instances
        """
        return await self.get_by_status(db, SessionStatus.ACTIVE)

    async def create(
        self, db: AsyncSession, *, obj_in: dict, owner_id: int | None = None
    ) -> Session:
        """Create a new session.

        Args:
            db: Database session
            obj_in: Dictionary with session data
            owner_id: Owner's user ID (if not in obj_in)

        Returns:
            Created Session instance
        """
        if "id" not in obj_in:
            obj_in["id"] = uuid.uuid4()
        if owner_id and "owner_id" not in obj_in:
            obj_in["owner_id"] = owner_id
        if "status" not in obj_in:
            obj_in["status"] = SessionStatus.ACTIVE
        return await super().create(db, obj_in=obj_in)


# Create instance
session_crud = CRUDSession(Session)

