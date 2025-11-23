"""SQL queries for debt information."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models.item import Item
from app.database.models.invoice import Invoice
from app.database.models.user import User
from app.database.sql.session import get_active_session_by_user_id
from app.database.sql.user import get_user_by_phone_number

logger = logging.getLogger(__name__)


async def get_my_debt_summary(db_session: AsyncSession, user_phone: str) -> dict:
    """Get complete debt summary for a user.
    
    Returns:
        dict with:
        - my_unpaid_items: Items I owe (debtor_id = me, is_paid = false)
        - untagged_items: Items without debtor in my session
        - total_debt: Total amount I owe
    """
    user = await get_user_by_phone_number(db_session, user_phone)
    if not user:
        return {
            "my_unpaid_items": [],
            "untagged_items": [],
            "total_debt": 0.0,
            "error": "Usuario no encontrado"
        }
    
    session = await get_active_session_by_user_id(db_session, user.id)
    if not session:
        return {
            "my_unpaid_items": [],
            "untagged_items": [],
            "total_debt": 0.0,
            "error": "No tienes una sesión activa"
        }
    
    # Query 1: Items asignados a mí que no están pagados
    my_items_result = await db_session.execute(
        select(Item, Invoice, User)
        .join(Invoice, Item.invoice_id == Invoice.id)
        .join(User, Invoice.payer_id == User.id)
        .where(Item.debtor_id == user.id)
        .where(Item.is_paid == False)
        .where(Invoice.session_id == session.id)
    )
    my_items_raw = my_items_result.all()
    
    # Procesar items míos
    my_unpaid_items = []
    total_debt = 0.0
    debt_by_person = {}  # creditor_name -> {items: [], total: float}
    
    for item, invoice, creditor in my_items_raw:
        item_data = {
            "item_id": item.id,
            "description": item.description,
            "amount": float(item.total),
            "invoice_description": invoice.description,
            "creditor_name": creditor.name,
            "creditor_phone": creditor.phone_number,
        }
        my_unpaid_items.append(item_data)
        total_debt += float(item.total)
        
        # Agrupar por acreedor
        if creditor.name not in debt_by_person:
            debt_by_person[creditor.name] = {
                "phone": creditor.phone_number,
                "items": [],
                "total": 0.0
            }
        debt_by_person[creditor.name]["items"].append(item_data)
        debt_by_person[creditor.name]["total"] += float(item.total)
    
    # Query 2: Items sin debtor en la sesión activa
    untagged_result = await db_session.execute(
        select(Item, Invoice, User)
        .join(Invoice, Item.invoice_id == Invoice.id)
        .join(User, Invoice.payer_id == User.id)
        .where(Item.debtor_id == None)
        .where(Item.is_paid == False)
        .where(Invoice.session_id == session.id)
    )
    untagged_raw = untagged_result.all()
    
    # Procesar items sin tag
    untagged_items = []
    for item, invoice, payer in untagged_raw:
        untagged_items.append({
            "item_id": item.id,
            "description": item.description,
            "amount": float(item.total),
            "invoice_description": invoice.description,
            "paid_by": payer.name,
        })
    
    return {
        "my_unpaid_items": my_unpaid_items,
        "untagged_items": untagged_items,
        "debt_by_person": debt_by_person,
        "total_debt": total_debt,
        "session_description": session.description,
    }


def format_debt_summary(summary: dict) -> str:
    """Format debt summary as WhatsApp message.
    
    Args:
        summary: Dict from get_my_debt_summary
        
    Returns:
        Formatted message string
    """
    if "error" in summary:
        return f"❌ {summary['error']}"
    
    lines = []
    
    # Header
    if summary["session_description"]:
        lines.append(f"📊 **Estado de deudas** - {summary['session_description']}\n")
    else:
        lines.append("📊 **Estado de deudas**\n")
    
    # My debts grouped by person
    if summary["debt_by_person"]:
        lines.append("💰 **A quién le debo:**")
        for creditor, data in summary["debt_by_person"].items():
            lines.append(f"\n👤 {creditor}:")
            for item in data["items"]:
                lines.append(f"  • {item['description']}: ${item['amount']:.0f}")
            lines.append(f"  **Subtotal: ${data['total']:.0f}**")
        
        lines.append(f"\n💵 **Total que debo: ${summary['total_debt']:.0f}**")
    else:
        lines.append("✅ No tienes deudas pendientes")
    
    # Untagged items
    if summary["untagged_items"]:
        lines.append("\n\n❓ **Items sin asignar:**")
        for item in summary["untagged_items"]:
            lines.append(
                f"  • {item['description']}: ${item['amount']:.0f} "
                f"(pagado por {item['paid_by']})"
            )
        lines.append("\n💡 *Estos items aún no tienen deudor asignado*")
    
    return "\n".join(lines)

