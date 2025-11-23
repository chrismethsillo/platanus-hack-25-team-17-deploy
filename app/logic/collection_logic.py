from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict
from app.database.sql.session import get_all_session_debtors_from_active_session
from app.database.models.user import User
from app.database.models.payment_method import PaymentMethod
from app.database.sql.payment import get_pending_items_by_user_id
from app.integrations.kapso import send_text_message
from app.database.sql.payment_methods import get_user_payment_methods


async def build_collection_message(
    db_session: AsyncSession, user: User, collector_id: int, collector_payment_methods: list[PaymentMethod]
) -> str:
    """Build a collection message for a user showing all their pending debts to a specific collector.

    Args:
        db_session: Database session
        user: User to build the message for (debtor)
        collector_id: ID of the collector (person who triggered collect and is the payer)
        collector_payment_methods: Payment methods of the collector

    Returns:
        Formatted message string with debts grouped by invoice
    """
    # Get all pending items for this user
    all_items = await get_pending_items_by_user_id(db_session, user.id)
    
    # Filter items to only show those where the collector is the payer
    items = [item for item in all_items if item.invoice.payer_id == collector_id]

    if not items:
        return "No tienes deudas pendientes con esta persona."

    # Group items by invoice
    items_by_invoice = defaultdict(list)
    for item in items:
        items_by_invoice[item.invoice].append(item)

    # Build message parts
    message_parts = []

    for invoice, invoice_items in items_by_invoice.items():
        # Calculate total from all items for this invoice
        total_from_all_items = sum(float(item.total) for item in invoice_items)

        # Get payer name
        payer_name = invoice.payer.name

        # Build the header for this invoice
        message_parts.append(f"Le debes a {payer_name} {total_from_all_items:.2f}:")

        # Build bullet list of items
        for item in invoice_items:
            item_description = item.description or "Sin descripción"
            item_total = float(item.total)
            message_parts.append(f"  • {item_description}: {item_total:.2f}")

        # Add blank line between invoices
        message_parts.append("")

    # Add collector's payment methods
    if collector_payment_methods:
        message_parts.append("Puedes pagar a:")
        for payment_method in collector_payment_methods:
            # Format bank account information nicely
            description = payment_method.description or ""
            if description:
                # If description contains multiple lines, format each line
                description_lines = description.split('\n')
                message_parts.append(f"• {payment_method.name}:")
                for line in description_lines:
                    message_parts.append(f"  {line}")
            else:
                message_parts.append(f"• {payment_method.name}")
    return "\n".join(message_parts).rstrip()


async def send_collection_message_to_all_debtors(
    db_session: AsyncSession, number: str, collector_id: int, collector_payment_methods: list[PaymentMethod]
) -> None:
    """Send collection messages to all debtors in the active session who owe money to the collector.
    
    Args:
        db_session: Database session
        number: Phone number of the user who triggered collect
        collector_id: ID of the collector (person who triggered collect)
        collector_payment_methods: Payment methods of the collector
    """
    users = await get_all_session_debtors_from_active_session(db_session, number)
    for user in users:
        message = await build_collection_message(db_session, user, collector_id, collector_payment_methods)
        # Only send message if there are debts to show
        if message != "No tienes deudas pendientes con esta persona.":
            send_text_message(user.phone_number, message)
