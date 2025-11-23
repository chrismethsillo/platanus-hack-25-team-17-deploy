"""CRUD operations for Item model."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.crud.base import CRUDBase
from app.database.models.item import Item


class CRUDItem(CRUDBase[Item]):
    """CRUD operations for Item model."""

    async def get_by_invoice(self, db: AsyncSession, invoice_id: int) -> list[Item]:
        """Get items by invoice ID.

        Args:
            db: Database session
            invoice_id: Invoice ID

        Returns:
            List of Item instances with debtor relationship loaded
        """
        result = await db.execute(
            select(Item)
            .options(selectinload(Item.debtor))
            .where(Item.invoice_id == invoice_id)
        )
        return list(result.scalars().all())

    async def get_by_debtor(self, db: AsyncSession, debtor_id: int) -> list[Item]:
        """Get items by debtor ID.

        Args:
            db: Database session
            debtor_id: Debtor's user ID

        Returns:
            List of Item instances
        """
        result = await db.execute(select(Item).where(Item.debtor_id == debtor_id))
        return list(result.scalars().all())

    async def get_unpaid_items(self, db: AsyncSession) -> list[Item]:
        """Get all unpaid items.

        Args:
            db: Database session

        Returns:
            List of unpaid Item instances
        """
        result = await db.execute(select(Item).where(Item.is_paid == False))
        return list(result.scalars().all())

    async def get_by_payment(self, db: AsyncSession, payment_id: int) -> list[Item]:
        """Get items by payment ID.

        Args:
            db: Database session
            payment_id: Payment ID

        Returns:
            List of Item instances
        """
        result = await db.execute(select(Item).where(Item.payment_id == payment_id))
        return list(result.scalars().all())


# Create instance
item_crud = CRUDItem(Item)

