from fastapi import APIRouter, Request, Response
from app.models.kapso import KapsoWebhookMessageReceived
from app.logic.message_receiver import handle_image_message, handle_text_message, check_existing_user_logic
from app.database import db_manager

router = APIRouter(prefix="/webhooks/kapso")


@router.post("/received", status_code=200)
def kapso_received_webhook(request: Request, payload: KapsoWebhookMessageReceived):
    try:
        db_session = db_manager.db_session()
        check_existing_user_logic(db_session, payload.message.conversation)
        if payload.message.is_image():
            handle_image_message(db_session, payload.message.image, payload.message.sender)
        elif payload.message.is_text():
            handle_text_message(db_session, payload.message.text, payload.message.sender)
    finally:
        return Response(status_code=200)
