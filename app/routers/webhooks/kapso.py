import logging
from fastapi import APIRouter, Request, Response
from app.models.kapso import KapsoWebhookMessageReceived
from app.logic.message_receiver import handle_image_message, handle_text_message, check_existing_user_logic
from app.database import db_manager

router = APIRouter(prefix="/webhooks/kapso")

logger = logging.getLogger(__name__)


@router.post("/received", status_code=200)
async def kapso_received_webhook(request: Request, payload: KapsoWebhookMessageReceived):
    """Handle incoming Kapso webhook messages.
    
    This endpoint processes both text and image messages from users.
    It ensures users have active sessions before processing receipts or commands.
    
    Args:
        request: FastAPI request object
        payload: Kapso webhook payload with message and conversation data
        
    Returns:
        Response with status 200
    """
    try:
        logger.info(f"Received webhook from {payload.conversation.phone_number}")
        
        # Get database session
        db_session = db_manager.db_session()
        
        # Ensure user exists in database
        check_existing_user_logic(db_session, payload.conversation)
        
        # Handle different message types
        if payload.message.is_image():
            logger.info(f"Processing image message from {payload.message.sender}")
            await handle_image_message(db_session, payload.message.image, payload.message.sender)
        elif payload.message.is_text():
            logger.info(f"Processing text message from {payload.message.sender}: {payload.message.text.body[:50]}")
            await handle_text_message(db_session, payload.message.text, payload.message.sender)
        else:
            logger.warning(f"Received unsupported message type from {payload.message.sender}")
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        # Still return 200 to acknowledge receipt to Kapso
    finally:
        return Response(status_code=200)
