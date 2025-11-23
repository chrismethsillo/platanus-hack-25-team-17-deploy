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
from app.database.sql.payment import get_pending_items_by_user_id, process_payment
from app.database.sql.session import (
    create_session,
    has_active_session,
    close_session,
    join_session,
    get_all_session_users,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.sql.user import get_user_by_phone_number, create_user


async def check_existing_user_logic(db_session: AsyncSession, conversation: KapsoConversation) -> None:
    logging.info(f"Checking existing user for conversation: {conversation}")
    current_user = await get_user_by_phone_number(db_session, conversation.phone_number)
    logging.info(f"Current user: {current_user}")
    if not current_user:
        try:
            await create_user(db_session, conversation.phone_number, conversation.contact_name)
            logging.info(f"Created new user for {conversation.phone_number}")
        except Exception as e:
            logging.error(f"Error creating user: {e}", exc_info=True)
            # Continue anyway, user might have been created by another request


async def check_user_has_active_session(db_session: AsyncSession, sender: str) -> bool:
    user = await get_user_by_phone_number(db_session, sender)
    if not user:
        return False
    return await has_active_session(db_session, user.id)


async def handle_receipt(db_session: AsyncSession, receipt: ReceiptExtraction, sender: str) -> None:
    """Handle receipt image processing.

    Args:
        db_session: Database session
        receipt: Extracted receipt data
        sender: User phone number
    """
    # Check if user has an active session
    if not await check_user_has_active_session(db_session, sender):
        send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
        return

    tip = receipt.tip / receipt.total_amount
    try:
        invoice, items = await create_invoice_with_items(db_session, receipt, tip, sender)
        send_text_message(sender, build_invoice_created_message(invoice, items))
    except MultipleResultsFound:
        send_text_message(sender, TOO_MANY_ACTIVE_SESSIONS_MESSAGE)
        return
    except NoResultFound:
        # This shouldn't happen now that we check for active session first
        send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
        return


async def handle_transfer(db_session: AsyncSession, transfer: TransferExtraction, sender: str) -> None:
    user = await get_user_by_phone_number(db_session, sender)
    if not user:
        send_text_message(sender, "Usuario no encontrado. Por favor, verifica tu número de teléfono.")
        return

    pending_items = await get_pending_items_by_user_id(db_session, user.id)

    if not pending_items:
        send_text_message(sender, "No tienes items pendientes de pago.")
        return

    total_pending = sum(float(item.total) for item in pending_items)
    transfer_amount = float(transfer.amount)

    tolerance = 0.01
    if abs(transfer_amount - total_pending) > tolerance:
        send_text_message(
            sender,
            f"El monto de la transferencia (${transfer_amount:.2f}) no coincide con el total pendiente (${total_pending:.2f}). "
            f"Por favor, verifica el monto.",
        )
        return

    first_invoice = pending_items[0].invoice
    receiver_id = first_invoice.payer_id

    try:
        await process_payment(
            db_session=db_session,
            payer_id=user.id,
            receiver_id=receiver_id,
            amount=transfer_amount,
            items_to_pay=pending_items,
        )

        send_text_message(
            sender,
            f"✅ Pago procesado exitosamente por ${transfer_amount:.2f}. "
            f"Se han marcado {len(pending_items)} item(s) como pagados.",
        )
    except Exception as e:
        await db_session.rollback()
        send_text_message(sender, f"❌ Error al procesar el pago: {str(e)}. Por favor, intenta nuevamente.")


async def handle_image_message(db_session: AsyncSession, image: KapsoImage, sender: str) -> None:
    image_content, mime_type = await download_image_from_url(image.link)
    ocr_result = await scan_receipt(image_content, mime_type)
    if ocr_result.document_type == ReceiptDocumentType.RECEIPT:
        await handle_receipt(db_session, ocr_result.receipt, sender)
    elif ocr_result.document_type == ReceiptDocumentType.TRANSFER:
        await handle_transfer(db_session, ocr_result.transfer, sender)



async def handle_voice_message(db_session: AsyncSession, conversation: KapsoConversation, sender: str) -> None:
    """
    Extrae la transcripción del mensaje de voz y la procesa con el agente.
    La transcripción se encuentra en conversation.kapso.last_message_text con formato "Transcript: ..."
    """
    if not conversation.kapso or not conversation.kapso.last_message_text:
        logging.warning(f"No se encontró transcripción para mensaje de voz de {sender}")
        return
    
    last_message_text = conversation.kapso.last_message_text
    
    # Buscar el prefijo "Transcript: " y extraer solo la transcripción
    transcript_prefix = "Transcript: "
    if transcript_prefix not in last_message_text:
        logging.warning(f"No se encontró el prefijo 'Transcript: ' en last_message_text: {last_message_text}")
        return
    
    # Encontrar la posición después de "Transcript: "
    transcript_start = last_message_text.find(transcript_prefix) + len(transcript_prefix)
    transcript = last_message_text[transcript_start:].strip()
    
    if not transcript:
        logging.warning(f"La transcripción está vacía para mensaje de voz de {sender}")
        return
    
    logging.info(f"Procesando transcripción de voz: {transcript[:100]}...")
    
    # Procesar la transcripción con el agente, igual que handle_text_message
    action_to_execute = await process_user_command(transcript)
    if action_to_execute.action == ActionType.CREATE_SESSION:
        session = await create_session(db_session, action_to_execute.create_session_data.description, sender)
        send_text_message(sender, build_session_id_link(session.id))


async def handle_text_message(db_session: AsyncSession, message_body: KapsoBody, sender: str) -> None:
    text_content = message_body.body if hasattr(message_body, "body") else str(message_body)

    action_to_execute = await process_user_command(text_content)

    if action_to_execute.action == ActionType.CREATE_SESSION:
        if await check_user_has_active_session(db_session, sender):
            send_text_message(sender, TOO_MANY_ACTIVE_SESSIONS_MESSAGE)
            return

        # Create new session
        session = await create_session(db_session, action_to_execute.create_session_data.description, sender)
        send_text_message(sender, SESSION_CREATED_MESSAGE)
        send_text_message(sender, build_session_id_link(session.id))

    elif action_to_execute.action == ActionType.CLOSE_SESSION:
        # Check if user has an active session
        if not await check_user_has_active_session(db_session, sender):
            send_text_message(sender, "No tienes una sesión activa para cerrar.")
            return

        # Get session ID from action data or from user's active session
        if action_to_execute.close_session_data and action_to_execute.close_session_data.session_id:
            session_id = action_to_execute.close_session_data.session_id
        else:
            # Get user's active session
            user = await get_user_by_phone_number(db_session, sender)
            from app.database.sql.session import get_active_session_by_user_id

            try:
                active_session = await get_active_session_by_user_id(db_session, user.id)
                if active_session:
                    session_id = str(active_session.id)
                else:
                    send_text_message(sender, "No se pudo encontrar tu sesión activa.")
                    return
            except (NoResultFound, MultipleResultsFound):
                send_text_message(sender, "No se pudo encontrar tu sesión activa.")
                return

        # Close the session
        try:
            # Get all users before closing to notify them
            all_users = await get_all_session_users(db_session, session_id)

            # Close the session (this will verify ownership)
            closed_session = await close_session(db_session, session_id, sender)

            # Get owner info
            owner_user = await get_user_by_phone_number(db_session, sender)

            # Send notification to all users
            for user_id, phone_number in all_users:
                is_owner = user_id == owner_user.id
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
            session, already_in_session = await join_session(db_session, session_id, sender)

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
        if not await check_user_has_active_session(db_session, sender):
            send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
            return
        # TODO: Implement assign item to user logic
        send_text_message(sender, "Función de asignación de items próximamente disponible.")

    elif action_to_execute.action == ActionType.UNKNOWN:
        # Check if user might need to create a session first
        if not await check_user_has_active_session(db_session, sender):
            send_text_message(
                sender,
                "No entendí tu mensaje. " + NO_ACTIVE_SESSION_MESSAGE,
            )
        else:
            send_text_message(sender, "No entendí tu mensaje. ¿Podrías reformularlo o pedir ayuda con 'ayuda'?")
