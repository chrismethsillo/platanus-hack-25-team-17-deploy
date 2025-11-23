from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, or_
from app.database.models.session import Session, SessionStatus, session_users
from app.database.models.user import User
from app.database.sql.user import get_user_by_phone_number, get_user_by_id
import uuid


async def get_active_session_by_user_id(db_session: AsyncSession, user_id: int) -> Session | None:
    result = await db_session.execute(
        select(Session).filter(or_(Session.owner_id == user_id, session_users.c.user_id == user_id)).filter(Session.status == SessionStatus.ACTIVE)
    )
    return result.scalar_one_or_none()


async def has_active_session(db_session: AsyncSession, user_id: int) -> bool:
    """Check if a user has an active session.

    This checks if the user is either owner or participant in an active session.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        True if user has an active session, False otherwise
    """
    try:
        result = await get_active_session_by_user_id(db_session, user_id)
        return result is not None
    except NoResultFound:
        return False


async def get_all_session_users(db_session: AsyncSession, session_id: str) -> list[tuple[int, str]]:
    """Get all users (owner + participants) in a session.

    Args:
        db_session: Database session
        session_id: Session UUID as string

    Returns:
        List of tuples (user_id, phone_number) for all users in the session
    """

    session_uuid = uuid.UUID(session_id)
    session = await get_session_by_id(db_session, session_id)

    # Get owner
    owner = await get_user_by_id(db_session, session.owner_id)
    users_list = [(owner.id, owner.phone_number)]

    # Get all participants from session_users table
    result = await db_session.execute(
        select(User.id, User.phone_number)
        .select_from(session_users)
        .join(User, session_users.c.user_id == User.id)
        .where(
            session_users.c.session_id == session_uuid,
            session_users.c.user_id != session.owner_id,  # Exclude owner to avoid duplicates
        )
    )
    participants = result.all()
    users_list.extend(participants)
    return users_list


async def close_session(db_session: AsyncSession, session_id: str, user_phone: str) -> Session:
    session = await get_session_by_id(db_session, session_id)
    user = await get_user_by_phone_number(db_session, user_phone)

    if not user:
        raise NoResultFound(f"User with phone {user_phone} not found")

    # Check if user is the owner
    if session.owner_id != user.id:
        raise ValueError("Solo el creador de la sesión puede cerrarla")

    session.status = SessionStatus.CLOSED
    await db_session.commit()
    await db_session.refresh(session)
    return session


async def create_session(db_session: AsyncSession, description: str, owner_number: str) -> Session:
    user = await get_user_by_phone_number(db_session, owner_number)
    session = Session(description=description, owner_id=user.id, status=SessionStatus.ACTIVE)
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


async def get_session_by_id(db_session: AsyncSession, session_id: str) -> Session:
    try:
        session_uuid = uuid.UUID(session_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid session ID format: {session_id}") from e

    result = await db_session.execute(select(Session).filter(Session.id == session_uuid))
    session = result.scalar_one_or_none()
    if not session:
        raise NoResultFound(f"Session with ID {session_id} not found")
    return session


async def join_session(db_session: AsyncSession, session_id: str, user_phone: str) -> tuple[Session, bool]:
    user = await get_user_by_phone_number(db_session, user_phone)
    if not user:
        raise NoResultFound(f"User with phone {user_phone} not found")

    # Get target session
    target_session = await get_session_by_id(db_session, session_id)

    # Check if target session is active
    if target_session.status != SessionStatus.ACTIVE:
        raise ValueError("No puedes unirte a una sesión cerrada")

    # Check if user is already in this session
    session_uuid = uuid.UUID(session_id)
    result = await db_session.execute(
        select(session_users).where(session_users.c.session_id == session_uuid, session_users.c.user_id == user.id)
    )
    existing_membership = result.first()

    if existing_membership:
        # User is already in the session
        return target_session, True

    # Close user's active session if exists and it's not the target session
    if await has_active_session(db_session, user.id):
        try:
            active_session = await get_active_session_by_user_id(db_session, user.id)
            # Only close if it's a different session
            if active_session and str(active_session.id) != session_id:
                active_session.status = SessionStatus.CLOSED
        except Exception:
            pass  # If there's an issue closing, continue

    # Add user to target session (many-to-many relationship)
    # Use insert directly on the association table to avoid lazy loading issues
    await db_session.execute(
        insert(session_users).values(session_id=session_uuid, user_id=user.id)
    )
    await db_session.commit()
    await db_session.refresh(target_session)

    return target_session, False
