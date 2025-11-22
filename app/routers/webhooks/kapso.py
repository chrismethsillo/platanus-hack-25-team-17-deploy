from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.models.kapso import KapsoWebhookMessageReceived
from app.logic.message_receiver import handle_image_message
from app.routers.deps import get_db
from app.config import settings

router = APIRouter(prefix="/webhooks/kapso")


def get_sync_session() -> Session:
    """Get a synchronous database session."""
    # Convert async database URL to sync
    db_url = settings.DATABASE_URL
    if hasattr(db_url, "unicode_string"):
        sync_url = db_url.unicode_string()
    else:
        sync_url = str(db_url)
    
    # Remove async driver if present
    sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@router.post("/received", status_code=200)
async def kapso_webhook(
    request: Request,
    payload: KapsoWebhookMessageReceived,
    db: AsyncSession = Depends(get_db),
):
    if payload.message.is_image():
        # Create sync session for synchronous functions
        sync_db = get_sync_session()
        try:
            await handle_image_message(
                sync_db,
                payload.message.image,
                payload.message.sender,
            )
        finally:
            sync_db.close()
    elif payload.message.is_text():
        pass
