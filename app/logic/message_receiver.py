import logging
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import select
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
from app.logic.collection_logic import send_collection_message_to_all_debtors
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.sql.user import get_user_by_phone_number, create_user
from app.logic.message_sender import send_message_to_all_session_users


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
        await send_message_to_all_session_users(
            db_session, invoice.session_id, build_invoice_created_message(invoice, items)
        )
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

    # Si el monto no coincide, mostrar información detallada pero no bloquear
    if abs(transfer_amount - total_pending) > tolerance:
        # Construir mensaje detallado con los items pendientes
        items_detail = []
        for item in pending_items:
            items_detail.append(f"  • {item.description or '(sin descripción)'}: ${item.total:.2f}")

        items_list = "\n".join(items_detail)

        if transfer_amount < total_pending:
            # Pago parcial - permitir pero informar
            send_text_message(
                sender,
                f"⚠️ El monto de la transferencia (${transfer_amount:.2f}) es menor que el total pendiente (${total_pending:.2f}).\n\n"
                f"📋 Tus items pendientes:\n{items_list}\n\n"
                f"Se procesará un pago parcial. El resto quedará pendiente.",
            )
            # Continuar con el procesamiento del pago parcial
        else:
            # Pago mayor - informar y no procesar
            send_text_message(
                sender,
                f"⚠️ El monto de la transferencia (${transfer_amount:.2f}) es mayor que el total pendiente (${total_pending:.2f}).\n\n"
                f"📋 Tus items pendientes:\n{items_list}\n\n"
                f"Por favor, verifica el monto de la transferencia.",
            )
            return

    # Si el monto coincide o es menor (pago parcial), procesar el pago
    first_invoice = pending_items[0].invoice
    receiver_id = first_invoice.payer_id

    # Si es pago parcial, seleccionar items hasta cubrir el monto
    items_to_pay = pending_items
    partial_payment_info = {}  # item_id -> amount_to_pay
    if transfer_amount < total_pending:
        # Seleccionar items en orden hasta cubrir el monto de la transferencia
        items_to_pay = []
        remaining_amount = transfer_amount
        for item in pending_items:
            if remaining_amount <= tolerance:
                break
            item_total = float(item.total)
            current_paid = float(item.paid_amount) if item.paid_amount else 0.0
            remaining_item_amount = item_total - current_paid

            if remaining_item_amount <= remaining_amount:
                # Item completo o casi completo
                items_to_pay.append(item)
                partial_payment_info[item.id] = remaining_item_amount
                remaining_amount -= remaining_item_amount
            else:
                # Pago parcial del item
                items_to_pay.append(item)
                partial_payment_info[item.id] = remaining_amount
                remaining_amount = 0
                break

    try:
        # Si es pago parcial, necesitamos manejar los items de manera diferente
        if transfer_amount < total_pending:
            # Crear pago pero no marcar todos los items como pagados completamente
            from app.database.models.payment import Payment

            payment = Payment(
                payer_id=user.id,
                receiver_id=receiver_id,
                amount=transfer_amount,
            )
            db_session.add(payment)
            await db_session.flush()

            # Actualizar items según el monto pagado
            for item in items_to_pay:
                item.payment_id = payment.id
                item_total = float(item.total)
                amount_to_pay = partial_payment_info.get(item.id, item_total)

                # Actualizar paid_amount
                current_paid = float(item.paid_amount) if item.paid_amount else 0.0
                new_paid = current_paid + amount_to_pay
                item.paid_amount = new_paid

                # Si el item está completamente pagado (o casi)
                if new_paid >= item_total - tolerance:
                    item.is_paid = True
                    item.paid_amount = item_total  # Asegurar que no exceda el total
                else:
                    # Pago parcial - mantener is_paid = False
                    item.is_paid = False

            # Actualizar invoice pending_amount
            from app.database.models.invoice import Invoice

            invoices_to_update = {}
            for item in items_to_pay:
                amount_to_pay = partial_payment_info.get(item.id, float(item.total))
                if item.invoice_id not in invoices_to_update:
                    invoices_to_update[item.invoice_id] = 0.0
                invoices_to_update[item.invoice_id] += amount_to_pay

            for invoice_id, paid_amount in invoices_to_update.items():
                result = await db_session.execute(select(Invoice).filter(Invoice.id == invoice_id))
                invoice = result.scalar_one_or_none()
                if invoice:
                    current_pending = float(invoice.pending_amount)
                    paid_amount_float = float(paid_amount)
                    invoice.pending_amount = max(0.0, current_pending - paid_amount_float)

            await db_session.commit()

            fully_paid = sum(1 for item in items_to_pay if item.is_paid)
            partial_paid = len(items_to_pay) - fully_paid

            message = f"✅ Pago parcial procesado por ${transfer_amount:.2f}.\n"
            if fully_paid > 0:
                message += f"  • {fully_paid} item(s) completamente pagado(s)\n"
            if partial_paid > 0:
                message += f"  • {partial_paid} item(s) con pago parcial\n"
            message += f"\nTotal pendiente restante: ${total_pending - transfer_amount:.2f}"

            send_text_message(sender, message)
        else:
            # Pago completo - usar la función existente
            await process_payment(
                db_session=db_session,
                payer_id=user.id,
                receiver_id=receiver_id,
                amount=transfer_amount,
                items_to_pay=items_to_pay,
            )

            send_text_message(
                sender,
                f"✅ Pago procesado exitosamente por ${transfer_amount:.2f}. "
                f"Se han marcado {len(items_to_pay)} item(s) como pagados.",
            )
    except Exception as e:
        await db_session.rollback()
        logging.error(f"Error processing payment: {e}", exc_info=True)
        send_text_message(sender, f"❌ Error al procesar el pago: {str(e)}. Por favor, intenta nuevamente.")


async def handle_payment_with_context(
    db_session: AsyncSession, 
    image: KapsoImage, 
    sender: str,
    context_message: str | None = None
) -> None:
    """Handle payment with optional context message.
    
    When user sends a message like "pagué una bebida y una pizza" with a transfer image,
    this function:
    1. Extracts payment intent from the message
    2. Processes the image to get payment amount
    3. Matches items using AI
    4. Processes the payment with proper logic (exact/more/less)
    
    Args:
        db_session: Database session
        image: Payment proof image
        sender: User phone number
        context_message: Optional message describing what was paid
    """
    from app.services.payment_agent import extract_payment_intent_from_message
    from app.services.payment_matcher import match_payment_to_items
    from app.database.sql.payment_processing import process_payment_result, get_payment_summary
    
    # Download and process image
    image_content, mime_type = await download_image_from_url(image.link)
    ocr_result = await scan_receipt(image_content, mime_type)
    
    # Only handle transfer documents for payment matching
    if ocr_result.document_type != ReceiptDocumentType.TRANSFER:
        # Fall back to regular receipt handling
        if ocr_result.document_type == ReceiptDocumentType.RECEIPT:
            await handle_receipt(db_session, ocr_result.receipt, sender)
        return
    
    transfer = ocr_result.transfer
    
    # If no context message, use old flow
    if not context_message:
        await handle_transfer(db_session, transfer, sender)
        return
    
    # Check if user has active session
    if not await check_user_has_active_session(db_session, sender):
        send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
        return
    
    try:
        # Extract payment intent from message
        logging.info(f"Extracting payment intent from message: {context_message}")
        payment_intent = await extract_payment_intent_from_message(context_message)
        
        if not payment_intent.is_payment or not payment_intent.items_paid:
            logging.warning("Message is not a payment intent, falling back to old flow")
            await handle_transfer(db_session, transfer, sender)
            return
        
        logging.info(f"Payment intent extracted: {payment_intent}")
        
        # Match items using AI
        payment_match = await match_payment_to_items(
            db_session,
            sender,
            payment_intent,
            transfer.amount,
        )
        
        logging.info(f"Payment match result: {payment_match}")
        
        if not payment_match.matched_items:
            send_text_message(
                sender,
                "❌ No se pudieron identificar los items mencionados. "
                "Por favor, verifica que los items existan en la sesión activa."
            )
            return
        
        # Process payment
        paid_items, remainder_item = await process_payment_result(
            db_session,
            payment_match,
            sender,
            payment_description=f"Pago: {context_message[:100]}",
        )
        
        # Send summary
        summary = await get_payment_summary(db_session, paid_items, remainder_item)
        send_text_message(sender, summary)
        
    except Exception as e:
        logging.error(f"Error processing payment with context: {e}", exc_info=True)
        send_text_message(
            sender,
            f"❌ Error al procesar el pago: {str(e)}. "
            "Por favor, intenta nuevamente o contacta soporte."
        )


async def handle_image_message(db_session: AsyncSession, image: KapsoImage, sender: str) -> None:
    """Handle image message without context.
    
    For backward compatibility, routes to appropriate handler.
    """
    await handle_payment_with_context(db_session, image, sender, context_message=None)


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

    if action_to_execute.action == ActionType.QUERY_DEBT_STATUS:
        # Handle debt status query
        from app.database.sql.debt_queries import get_my_debt_summary, format_debt_summary
        
        summary = await get_my_debt_summary(db_session, sender)
        formatted_message = format_debt_summary(summary)
        send_text_message(sender, formatted_message)
        return

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

        # Get the active session and user
        current_user = await get_user_by_phone_number(db_session, sender)
        from app.database.sql.session import get_active_session_by_user_id

        active_session = await get_active_session_by_user_id(db_session, current_user.id)

        if not active_session:
            send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
            return

        # Get assignment data
        assign_data = action_to_execute.assign_item_to_user_data
        if not assign_data:
            send_text_message(
                sender, "No se pudo identificar qué item asignar. Por favor, especifica el item y el usuario."
            )
            return

        # Determine the user to assign to
        # If no user_name is provided, assume the sender is consuming the item
        user_name = assign_data.user_name
        user_id = assign_data.user_id

        if not user_name and not user_id:
            # Default to sender
            user_id = current_user.id
            user_name = None

        # Find items in the active session
        from sqlalchemy import select
        from app.database.models.item import Item
        from app.database.models.invoice import Invoice

        # Build query to find items in the active session
        query = select(Item).join(Invoice, Item.invoice_id == Invoice.id).where(Invoice.session_id == active_session.id)

        # Filter by item_id if provided
        if assign_data.item_id:
            query = query.where(Item.id == assign_data.item_id)
        # Filter by item_description if provided
        elif assign_data.item_description:
            query = query.where(Item.description.ilike(f"%{assign_data.item_description}%"))
        else:
            send_text_message(sender, "Por favor, especifica qué item quieres asignar (por descripción o ID).")
            return

        # Prefer unassigned items (debtor_id is None)
        query = query.where(Item.debtor_id.is_(None))

        result = await db_session.execute(query)
        items = result.scalars().all()

        if not items:
            send_text_message(
                sender,
                f"No se encontraron items sin asignar que coincidan con '{assign_data.item_description or f'ID {assign_data.item_id}'}' en tu sesión activa.",
            )
            return

        # Si hay múltiples items con la misma descripción, asignar el primero disponible
        # (el sistema ya filtra por items sin asignar, así que cualquiera es válido)
        if len(items) > 1:
            logging.info(
                f"Se encontraron {len(items)} items con la descripción '{assign_data.item_description}'. "
                f"Asignando el primero disponible (ID: {items[0].id})"
            )

        item = items[0]

        # Find the user to assign to
        from app.database.sql.user import get_user_by_id
        from sqlalchemy import select
        from app.database.models.user import User

        assigned_user = None
        if user_id:
            assigned_user = await get_user_by_id(db_session, user_id)
        elif user_name:
            result = await db_session.execute(select(User).where(User.name.ilike(f"%{user_name}%")))
            users = result.scalars().all()
            if users:
                assigned_user = users[0] if len(users) == 1 else users[0]  # Use first match

        if not assigned_user:
            send_text_message(sender, f"❌ No se pudo encontrar al usuario{' ' + user_name if user_name else ''}.")
            return

        # Assign the item by updating debtor_id
        item.debtor_id = assigned_user.id
        await db_session.commit()
        await db_session.refresh(item)

        # Send confirmation message
        message = f"✅ Item '{item.description}' asignado a {assigned_user.name} (${item.total:.2f})"
        send_text_message(sender, message)

    elif action_to_execute.action == ActionType.UNKNOWN:
        # Check if user might need to create a session first
        if not await check_user_has_active_session(db_session, sender):
            send_text_message(
                sender,
                "No entendí tu mensaje. " + NO_ACTIVE_SESSION_MESSAGE,
            )
        else:
            send_text_message(sender, "No entendí tu mensaje. ¿Podrías reformularlo o pedir ayuda con 'ayuda'?")
    elif action_to_execute.action == ActionType.COLLECT:
        if not await check_user_has_active_session(db_session, sender):
            send_text_message(sender, NO_ACTIVE_SESSION_MESSAGE)
            return
        await send_collection_message_to_all_debtors(db_session, sender)
