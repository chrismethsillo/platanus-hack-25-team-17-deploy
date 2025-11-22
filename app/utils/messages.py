from app.database.models.invoice import Invoice
from app.database.models.item import Item
from uuid import UUID
from urllib.parse import quote
from app.config.settings import settings
from app.core.logging import get_logger

TOO_MANY_ACTIVE_SESSIONS_MESSAGE = (
    "No puedes tener más de una sesión activa a la vez, por favor cierra la sesión anterior antes de crear una nueva."
)

NO_ACTIVE_SESSION_MESSAGE = (
    "No tienes una sesión de cobro activa. 🔒\n\n"
    "Para comenzar a registrar boletas y gestionar pagos, necesitas crear una sesión.\n\n"
    "Puedes decir:\n"
    "• 'Crear sesión para la cena de hoy'\n"
    "• 'Nueva sesión'\n"
    "• O simplemente 'crear sesión'"
)

SESSION_CREATED_MESSAGE = (
    "¡Sesión creada exitosamente! ✅\n\n"
    "Ahora puedes:\n"
    "• Enviar fotos de boletas para registrarlas\n"
    "• Asignar items a personas\n"
    "• Ver el estado de los pagos\n\n"
    "Comparte este link con otros para que se unan a la sesión:"
)

def build_session_closed_message(session_description: str, is_owner: bool) -> str:
    """Build session closed message based on user role.

    Args:
        session_description: Description of the closed session
        is_owner: Whether the user is the owner
    
    Returns:
        Formatted message
    """
    if is_owner:
        return (
            f"Has cerrado la sesión '{session_description or 'Sin descripción'}' exitosamente. ✅\n\n"
            f"Se ha notificado a todos los participantes.\n"
            f"Ya no se pueden agregar más boletas a esta sesión."
        )
    else:
        return (
            f"La sesión '{session_description or 'Sin descripción'}' ha sido cerrada por el creador. 🔒\n\n"
            f"Ya no se pueden agregar más boletas a esta sesión.\n"
            f"Gracias por participar!"
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
    """Build a WhatsApp link to join a session.

    Args:
        session_id: UUID of the session

    Returns:
        WhatsApp link with URL-encoded message
    """
    if settings.KAPSO_PHONE_NUMBER is None:
        logger.error("KAPSO_PHONE_NUMBER is not set")
        return "No se puede generar el link de la sesión de cobro porque el número de teléfono de Kapso no está configurado."

    # Create a descriptive message for joining the session
    message = f"Me quiero unir a la sesión {session_id}"
    
    # URL encode the message for WhatsApp
    encoded_message = quote(message, safe='')
    
    return f"https://wa.me/{settings.KAPSO_PHONE_NUMBER}?text={encoded_message}"
