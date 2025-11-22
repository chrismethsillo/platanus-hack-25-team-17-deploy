"""CRUD operations for Invoice model."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base import CRUDBase
from app.database.models.invoice import Invoice


class CRUDInvoice(CRUDBase[Invoice]):
    """CRUD operations for Invoice model."""

    async def get_by_payer(self, db: AsyncSession, payer_id: int) -> list[Invoice]:
        """Get invoices by payer ID.

        Args:
            db: Database session
            payer_id: Payer's user ID

        Returns:
            List of Invoice instances
        """
        result = await db.execute(select(Invoice).where(Invoice.payer_id == payer_id))
        return list(result.scalars().all())

    async def get_by_session(self, db: AsyncSession, session_id) -> list[Invoice]:
        """Get invoices by session ID.

        Args:
            db: Database session
            session_id: Session UUID

        Returns:
            List of Invoice instances
        """
        result = await db.execute(select(Invoice).where(Invoice.session_id == session_id))
        return list(result.scalars().all())

    async def get_pending_invoices(self, db: AsyncSession) -> list[Invoice]:
        """Get all invoices with pending amounts.

        Args:
            db: Database session

        Returns:
            List of Invoice instances with pending_amount > 0
        """
        result = await db.execute(select(Invoice).where(Invoice.pending_amount > 0))
        return list(result.scalars().all())


# Create instance
invoice_crud = CRUDInvoice(Invoice)

