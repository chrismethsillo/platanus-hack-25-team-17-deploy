from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models.session import Session, SessionStatus, session_users
from app.database.sql.user import get_user_by_phone_number


async def get_active_session_by_user_id(db_session: AsyncSession, user_id: int) -> Session | None:
    result = await db_session.execute(
        select(Session).filter(Session.owner_id == user_id).filter(Session.status == SessionStatus.ACTIVE)
    )
    return result.scalar_one()


async def create_session(db_session: AsyncSession, description: str, owner_number: str) -> Session:
    user = await get_user_by_phone_number(db_session, owner_number)
    session = Session(description=description, owner_id=user.id, status=SessionStatus.ACTIVE)
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


async def get_sessions_by_user_id(db_session: AsyncSession, user_id: int) -> list[Session]:
    """Get all sessions where a user is involved (as owner or participant).

    Args:
        db_session: Database session
        user_id: ID of the user

    Returns:
        List of sessions where the user is involved
    """
    result = await db_session.execute(
        select(Session)
        .join(session_users, Session.id == session_users.c.session_id)
        .filter(session_users.c.user_id == user_id)
        .filter(Session.status == SessionStatus.ACTIVE)
    )
    return list(result.scalars().all())
