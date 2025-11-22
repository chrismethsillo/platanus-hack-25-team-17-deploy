from app.models.receipt import ReceiptExtraction
from sqlalchemy.orm import Session
from app.database.models.invoice import Invoice
from app.database.models.item import Item
from app.database.sql.user import get_user_by_phone_number
from app.database.sql.session import get_active_session_by_user_id


def create_invoice_with_items(
    db_session: Session, receipt: ReceiptExtraction, tip: float, sender: str
) -> tuple[Invoice, list[Item]]:
    user = get_user_by_phone_number(db_session, sender)
    session = get_active_session_by_user_id(db_session, user.id)
    invoice = Invoice(
        description=receipt.description,
        total=receipt.total_amount,
        pending_amount=receipt.total_amount,
        payer_id=user.id,
        session_id=session.id,
    )
    db_session.add(invoice)
    db_session.flush()
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
    db_session.commit()
    return invoice, items
