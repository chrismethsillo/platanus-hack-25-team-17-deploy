import logging
from sqlalchemy.orm.exc import NoResultFound
from app.services.ocr_service import download_image_from_url, scan_receipt
from app.models.kapso import KapsoImage, KapsoBody, KapsoConversation
from app.models.receipt import ReceiptExtraction, TransferExtraction, ReceiptDocumentType
from app.database.sql.invoice import create_invoice_with_items
from app.integrations.kapso import send_text_message
from sqlalchemy.orm.exc import MultipleResultsFound
from app.utils.messages import (
    TOO_MANY_ACTIVE_SESSIONS_MESSAGE,
    NO_ACTIVE_SESSION_MESSAGE,
    SESSION_CREATED_MESSAGE,
    build_session_closed_message,
    build_invoice_created_message,
    build_session_id_link,
)
from app.services.agent.processor import process_user_command
from app.models.text_agent import ActionType
from app.database.sql.session import (
    create_session,
    has_active_session,
    close_session,
    join_session,
    get_all_session_users,
)
from sqlalchemy.orm import Session
from app.database.sql.user import get_user_by_phone_number, create_user


def check_existing_user_logic(db_session: Session, conversation: KapsoConversation) -> None:
    """Ensure user exists in database, create if not.

    Args:
        db_session: Database session
        conversation: Conversation data from Kapso webhook
    """
    logging.info(f"Checking existing user for conversation: {conversation}")
    current_user = get_user_by_phone_number(db_session, conversation.phone_number)
    logging.info(f"Current user: {current_user}")
    if not current_user:
        try:
            create_user(db_session, conversation.phone_number, conversation.contact_name)
            logging.info(f"Created new user for {conversation.phone_number}")
        except Exception as e:
            logging.error(f"Error creating user: {e}", exc_info=True)
            # Continue anyway, user might have been created by another request


def check_user_has_active_session(db_session: Session, sender: str) -> bool:
    """Check if user has an active session.

    Args:
        db_session: Database session
        sender: User phone number

    Returns:
        True if user has active session, False otherwise
    """
    user = get_user_by_phone_number(db_session, sender)
    if not user:
        return False
    return has_active_session(db_session, user.id)


def handle_receipt(db_session: Session, receipt: ReceiptExtraction, sender: str) -> None:
    """Handle receipt image processing.

    Args:
        db_session: Database session
        receipt: Extracted receipt data
        sender: User phone number
    """
    # Check if user has an active session
    if not check_user_has_active_session(db_session, sender):
        send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
        return

    tip = receipt.tip / receipt.total_amount
    try:
        invoice, items = create_invoice_with_items(db_session, receipt, tip, sender)
        send_text_message(sender, build_invoice_created_message(invoice, items))
        send_text_message(sender, "Para compartir la sesión de cobro con más personas, comparte el siguiente mensaje:")
        send_text_message(sender, build_session_id_link(invoice.session_id))
    except MultipleResultsFound:
        send_text_message(sender, TOO_MANY_ACTIVE_SESSIONS_MESSAGE)
        return
    except NoResultFound:
        # This shouldn't happen now that we check for active session first
        send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
        return


def handle_transfer(db_session: Session, transfer: TransferExtraction) -> None:
    pass


async def handle_image_message(db_session: Session, message: KapsoImage, sender: str) -> None:
    image_content, mime_type = await download_image_from_url(message.link)
    ocr_result = await scan_receipt(image_content, mime_type)
    if ocr_result.document_type == ReceiptDocumentType.RECEIPT:
        handle_receipt(db_session, ocr_result.receipt, sender)
    elif ocr_result.document_type == ReceiptDocumentType.TRANSFER:
        handle_transfer(db_session, ocr_result.transfer)


async def handle_text_message(db_session: Session, message_body: KapsoBody, sender: str) -> None:
    """Handle text message from user.

    Args:
        db_session: Database session
        message_body: Text message body data
        sender: User phone number
    """
    # Extract text from message body
    text_content = message_body.body if hasattr(message_body, 'body') else str(message_body)
    
    action_to_execute = await process_user_command(text_content)

    if action_to_execute.action == ActionType.CREATE_SESSION:
        # Check if user already has an active session
        if check_user_has_active_session(db_session, sender):
            send_text_message(sender, TOO_MANY_ACTIVE_SESSIONS_MESSAGE)
            return

        # Create new session
        session = create_session(db_session, action_to_execute.create_session_data.description, sender)
        send_text_message(sender, SESSION_CREATED_MESSAGE)
        send_text_message(sender, build_session_id_link(session.id))

    elif action_to_execute.action == ActionType.CLOSE_SESSION:
        # Check if user has an active session
        if not check_user_has_active_session(db_session, sender):
            send_text_message(sender, "No tienes una sesión activa para cerrar.")
            return

        # Get session ID from action data or from user's active session
        if action_to_execute.close_session_data and action_to_execute.close_session_data.session_id:
            session_id = action_to_execute.close_session_data.session_id
        else:
            # Get user's active session
            user = get_user_by_phone_number(db_session, sender)
            from app.database.sql.session import get_active_session_by_user_id

            try:
                active_session = get_active_session_by_user_id(db_session, user.id)
                session_id = str(active_session.id)
            except (NoResultFound, MultipleResultsFound):
                send_text_message(sender, "No se pudo encontrar tu sesión activa.")
                return

        # Close the session
        try:
            # Get all users before closing to notify them
            all_users = get_all_session_users(db_session, session_id)
            
            # Close the session (this will verify ownership)
            closed_session = close_session(db_session, session_id, sender)
            
            # Get owner info
            owner_user = get_user_by_phone_number(db_session, sender)
            
            # Send notification to all users
            for user_id, phone_number in all_users:
                is_owner = (user_id == owner_user.id)
                message = build_session_closed_message(closed_session.description, is_owner)
                send_text_message(phone_number, message)
                
            logging.info(f"Session {session_id} closed and {len(all_users)} users notified")
            
        except NoResultFound:
            send_text_message(sender, "No se encontró la sesión especificada.")
        except ValueError as e:
            # User is not the owner
            send_text_message(sender, str(e))

    elif action_to_execute.action == ActionType.JOIN_SESSION:
        # Join a session by ID
        if not action_to_execute.join_session_data or not action_to_execute.join_session_data.session_id:
            send_text_message(sender, "No se pudo identificar el ID de la sesión. Por favor envía un ID válido.")
            return

        session_id = action_to_execute.join_session_data.session_id

        try:
            # Join the session (this will close any active session first)
            session, already_in_session = join_session(db_session, session_id, sender)
            
            if already_in_session:
                send_text_message(
                    sender,
                    f"Ya estás participando en esta sesión. ✅\n\n"
                    f"Descripción: {session.description or 'Sin descripción'}\n\n"
                    f"Puedes enviar boletas y continuar participando normalmente.",
                )
            else:
                send_text_message(
                    sender,
                    f"¡Te has unido exitosamente a la sesión! 🎉\n\n"
                    f"Descripción: {session.description or 'Sin descripción'}\n\n"
                    f"Ahora puedes enviar boletas y participar en esta sesión compartida con tus amigos.",
                )
        except NoResultFound:
            send_text_message(sender, "No se encontró la sesión especificada. Verifica que el ID sea correcto.")
        except ValueError as e:
            send_text_message(sender, f"Error: {str(e)}")
        except Exception as e:
            logging.error(f"Error joining session: {str(e)}", exc_info=True)
            send_text_message(sender, "Hubo un error al unirse a la sesión. Por favor intenta de nuevo.")

    elif action_to_execute.action == ActionType.ASSIGN_ITEM_TO_USER:
        # For assign item actions, check if user has active session
        if not check_user_has_active_session(db_session, sender):
            send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
            return
        # TODO: Implement assign item to user logic
        send_text_message(sender, "Función de asignación de items próximamente disponible.")

    elif action_to_execute.action == ActionType.UNKNOWN:
        # Check if user might need to create a session first
        if not check_user_has_active_session(db_session, sender):
            send_text_message(
                sender,
                "No entendí tu mensaje. " + NO_ACTIVE_SESSION_MESSAGE,
            )
        else:
            send_text_message(
                sender, "No entendí tu mensaje. ¿Podrías reformularlo o pedir ayuda con 'ayuda'?"
            )
