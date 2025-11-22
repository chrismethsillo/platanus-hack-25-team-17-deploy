import logging
from app.models.receipt import ReceiptExtraction
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.invoice import Invoice
from app.database.models.item import Item
from app.database.sql.user import get_user_by_phone_number
from app.database.sql.session import get_active_session_by_user_id


async def create_invoice_with_items(
    db_session: AsyncSession, receipt: ReceiptExtraction, tip: float, sender: str
) -> tuple[Invoice, list[Item]]:
    logging.info(f"Creating invoice with items for receipt: {receipt}")
    user = await get_user_by_phone_number(db_session, sender)
    session = await get_active_session_by_user_id(db_session, user.id)
    logging.info(f"Session: {session}")
    invoice = Invoice(
        description=receipt.merchant,
        total=receipt.total_amount,
        pending_amount=receipt.total_amount,
        payer_id=user.id,
        session_id=session.id,
    )
    db_session.add(invoice)
    await db_session.flush()
    items = []
    for item in receipt.items:
        for _ in range(item.count):
            item = Item(
                description=item.description,
                invoice_id=invoice.id,
                debtor_id=None,
                unit_price=item.amount,
                paid_amount=0,
                tip=tip,
                total=item.amount * (1 + tip),
                is_paid=False,
                payment_id=None,
            )
            db_session.add(item)
            items.append(item)
    await db_session.commit()
    return invoice, items
