from app.database.models.invoice import Invoice
from app.database.models.item import Item
from uuid import UUID
from app.config.settings import settings
from app.core.logging import get_logger

TOO_MANY_ACTIVE_SESSIONS_MESSAGE = (
    "No puedes tener más de una sesión activa a la vez, por favor cierra la sesión anterior antes de crear una nueva."
)

logger = get_logger(__name__)


def build_invoice_created_message(invoice: Invoice, items: list[Item]) -> str:
    message_parts = ["Boleta ingresada correctamente.\n"]
    message_parts.append(f"{invoice.description}, Total: {invoice.total}")
    message_parts.append("Detalle:")
    for item in items:
        tip_part = f"tip: {item.tip * 100}%," if item.tip > 0 else ""
        message_parts.append(f"• {item.description}, {item.unit_price}, {tip_part} total: {item.total}")
    return "\n".join(message_parts)


def build_session_id_link(session_id: UUID) -> str:
    if settings.KAPSO_PHONE_NUMBER is None:
        logger.error("KAPSO_PHONE_NUMBER is not set")
        return "No se puede generar el link de la sesión de cobro porque el número de teléfono de Kapso no está configurado."
    return f"Unete a mi sesión de cobro: https://wa.me/{settings.KAPSO_PHONE_NUMBER}?text={session_id}"
