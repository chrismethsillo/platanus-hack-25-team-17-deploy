"""Payment-related SQL operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.database.models.payment import Payment
from app.database.models.item import Item
from app.database.models.invoice import Invoice
from app.database.models.session import Session as SessionModel, session_users, SessionStatus


async def get_pending_items_by_user_id(db_session: AsyncSession, user_id: int) -> list[Item]:
    """Get all pending items for a user across all their active sessions.

    Args:
        db_session: Database session
        user_id: ID of the user (debtor)

    Returns:
        List of items where the user is the debtor and is_paid is False
    """
    result = await db_session.execute(
        select(Item)
        .join(Invoice, Item.invoice_id == Invoice.id)
        .join(SessionModel, Invoice.session_id == SessionModel.id)
        .join(session_users, SessionModel.id == session_users.c.session_id)
        .filter(
            and_(
                Item.debtor_id == user_id,
                Item.is_paid == False,
                session_users.c.user_id == user_id,
                SessionModel.status == SessionStatus.ACTIVE,
            )
        )
    )
    return list(result.scalars().all())


async def process_payment(
    db_session: AsyncSession,
    payer_id: int,
    receiver_id: int,
    amount: float,
    items_to_pay: list[Item],
) -> Payment:
    """Process a payment by creating a Payment record and updating items.

    This function:
    1. Creates a Payment record
    2. Associates items with the payment
    3. Marks items as paid
    4. Updates invoice pending_amount

    Args:
        db_session: Database session
        payer_id: ID of the user making the payment
        receiver_id: ID of the user receiving the payment
        amount: Payment amount
        items_to_pay: List of items to mark as paid

    Returns:
        Created Payment object
    """
    # Create payment
    payment = Payment(
        payer_id=payer_id,
        receiver_id=receiver_id,
        amount=amount,
    )
    db_session.add(payment)
    await db_session.flush()  # Get payment.id

    # Track invoices to update
    invoices_to_update = {}

    # Associate items with payment and mark as paid
    for item in items_to_pay:
        item.payment_id = payment.id
        item.is_paid = True
        item.paid_amount = item.total

        # Track invoice for pending_amount update (convert to float to avoid Decimal issues)
        item_total = float(item.total)
        if item.invoice_id not in invoices_to_update:
            invoices_to_update[item.invoice_id] = 0.0
        invoices_to_update[item.invoice_id] += item_total

    # Update invoice pending_amount
    for invoice_id, paid_amount in invoices_to_update.items():
        result = await db_session.execute(select(Invoice).filter(Invoice.id == invoice_id))
        invoice = result.scalar_one_or_none()
        if invoice:
            # Ensure both values are float before arithmetic
            current_pending = float(invoice.pending_amount)
            paid_amount_float = float(paid_amount)
            invoice.pending_amount = max(0.0, current_pending - paid_amount_float)

    await db_session.commit()
    return payment
