import logging
from sqlalchemy.orm.exc import NoResultFound
from app.services.ocr_service import download_image_from_url, scan_receipt
from app.models.kapso import KapsoImage, KapsoTextMessage, KapsoConversation
from app.models.receipt import ReceiptExtraction, TransferExtraction, ReceiptDocumentType
from app.database.sql.invoice import create_invoice_with_items
from app.integrations.kapso import send_text_message
from sqlalchemy.orm.exc import MultipleResultsFound
from app.utils.messages import TOO_MANY_ACTIVE_SESSIONS_MESSAGE, build_invoice_created_message, build_session_id_link
from app.database.sql.payment import get_pending_items_by_user_id, process_payment
from app.services.agent.processor import process_user_command
from app.models.text_agent import ActionType
from app.database.sql.session import create_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.sql.user import get_user_by_phone_number, create_user


async def check_existing_user_logic(db_session: AsyncSession, conversation: KapsoConversation) -> None:
    logging.info(f"Checking existing user for conversation: {conversation}")
    current_user = await get_user_by_phone_number(db_session, conversation.phone_number)
    logging.info(f"Current user: {current_user}")
    if not current_user:
        await create_user(db_session, conversation.phone_number, conversation.contact_name)


async def handle_receipt(db_session: AsyncSession, receipt: ReceiptExtraction, sender: str) -> None:
    tip = receipt.tip / receipt.total_amount
    try:
        invoice, items = await create_invoice_with_items(db_session, receipt, tip, sender)
        send_text_message(sender, build_invoice_created_message(invoice, items))
        send_text_message(sender, "Para compartir la sesión de cobro con más personas, comparte el siguiente mensaje:")
        send_text_message(sender, build_session_id_link(invoice.session_id))
    except MultipleResultsFound:
        send_text_message(sender, TOO_MANY_ACTIVE_SESSIONS_MESSAGE)
        return
    except NoResultFound:
        send_text_message(
            sender,
            "No hay sesión de cobro activa para este usuario. Envia un id de sesión para unirte a una, o puedes elegir crear una nueva sesión de cobro.",
        )
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
        payment = await process_payment(
            db_session=db_session,
            payer_id=user.id,
            receiver_id=receiver_id,
            amount=transfer_amount,
            items_to_pay=pending_items,
        )

        await db_session.commit()
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


async def handle_text_message(db_session: AsyncSession, message: KapsoTextMessage, sender: str) -> None:
    action_to_execute = await process_user_command(message.text.body)
    if action_to_execute.action == ActionType.CREATE_SESSION:
        session = await create_session(db_session, action_to_execute.create_session_data.description, sender)
        send_text_message(sender, build_session_id_link(session.id))
