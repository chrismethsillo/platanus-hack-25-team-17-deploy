from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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
        logging.error(f"Error getting user by phone number: {e}", exc_info=True)
        return None


async def create_user(db_session: AsyncSession, phone_number: str, name: str) -> None:
    user = User(phone_number=phone_number, name=name)
    db_session.add(user)
    await db_session.commit()


async def get_user_by_id(db_session: AsyncSession, user_id: int) -> User | None:
    result = await db_session.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()
