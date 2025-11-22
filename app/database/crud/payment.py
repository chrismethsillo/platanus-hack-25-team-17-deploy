"""CRUD operations for Payment model."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base import CRUDBase
from app.database.models.payment import Payment


class CRUDPayment(CRUDBase[Payment]):
    """CRUD operations for Payment model."""

    async def get_by_payer(self, db: AsyncSession, payer_id: int) -> list[Payment]:
        """Get payments by payer ID.

        Args:
            db: Database session
            payer_id: Payer's user ID

        Returns:
            List of Payment instances
        """
        result = await db.execute(select(Payment).where(Payment.payer_id == payer_id))
        return list(result.scalars().all())

    async def get_by_receiver(self, db: AsyncSession, receiver_id: int) -> list[Payment]:
        """Get payments by receiver ID.

        Args:
            db: Database session
            receiver_id: Receiver's user ID

        Returns:
            List of Payment instances
        """
        result = await db.execute(select(Payment).where(Payment.receiver_id == receiver_id))
        return list(result.scalars().all())

    async def get_between_users(
        self, db: AsyncSession, payer_id: int, receiver_id: int
    ) -> list[Payment]:
        """Get payments between two users.

        Args:
            db: Database session
            payer_id: Payer's user ID
            receiver_id: Receiver's user ID

        Returns:
            List of Payment instances
        """
        result = await db.execute(
            select(Payment).where(
                Payment.payer_id == payer_id, Payment.receiver_id == receiver_id
            )
        )
        return list(result.scalars().all())


# Create instance
payment_crud = CRUDPayment(Payment)

