from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models.user import User
import logging


async def get_user_by_phone_number(db_session: AsyncSession, phone_number: str) -> User | None:
    logging.info(f"Getting user by phone number: {phone_number}")
    try:
        result = await db_session.execute(select(User).filter(User.phone_number == phone_number))
        user = result.scalar_one_or_none()
        logging.info(f"User: {user}")
        return user
    except Exception as e:
        logging.info(f"Error getting user by phone number: {e}")
        return None


async def create_user(db_session: AsyncSession, phone_number: str, name: str) -> None:
    user = User(phone_number=phone_number, name=name)
    db_session.add(user)
    await db_session.commit()
