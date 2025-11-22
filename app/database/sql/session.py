from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import NoResultFound
from app.database.models.session import Session, SessionStatus
from app.database.sql.user import get_user_by_phone_number
import uuid


def get_active_session_by_user_id(db_session: DBSession, user_id: int) -> Session | None:
    """Get the active session for a user.

    This looks for sessions where the user is either the owner or a participant.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        Session if found, None otherwise

    Raises:
        MultipleResultsFound: If multiple active sessions are found
        NoResultFound: If no active session is found
    """
    from app.database.models.user import User

    # First try to find session where user is owner
    owner_session = (
        db_session.query(Session)
        .filter(Session.owner_id == user_id)
        .filter(Session.status == SessionStatus.ACTIVE)
        .one_or_none()
    )

    if owner_session:
        return owner_session

    # If not owner, check if user is a participant in any active session
    user = db_session.query(User).filter(User.id == user_id).one()
    for session in user.sessions:
        if session.status == SessionStatus.ACTIVE:
            return session

    # If no active session found, raise NoResultFound
    raise NoResultFound(f"No active session found for user {user_id}")


def has_active_session(db_session: DBSession, user_id: int) -> bool:
    """Check if a user has an active session.

    This checks if the user is either owner or participant in an active session.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        True if user has an active session, False otherwise
    """
    try:
        get_active_session_by_user_id(db_session, user_id)
        return True
    except NoResultFound:
        return False


def get_all_session_users(db_session: DBSession, session_id: str) -> list[tuple[int, str]]:
    """Get all users (owner + participants) in a session.

    Args:
        db_session: Database session
        session_id: Session UUID as string

    Returns:
        List of tuples (user_id, phone_number) for all users in the session
    """
    from app.database.models.user import User
    from app.database.models.session import session_users
    from sqlalchemy import select
    
    session_uuid = uuid.UUID(session_id)
    session = get_session_by_id(db_session, session_id)
    
    # Get owner
    owner = db_session.query(User).filter(User.id == session.owner_id).one()
    users_list = [(owner.id, owner.phone_number)]
    
    # Get all participants from session_users table
    participants = db_session.execute(
        select(User.id, User.phone_number)
        .select_from(session_users)
        .join(User, session_users.c.user_id == User.id)
        .where(
            session_users.c.session_id == session_uuid,
            session_users.c.user_id != session.owner_id  # Exclude owner to avoid duplicates
        )
    ).all()
    
    users_list.extend(participants)
    return users_list


def close_session(db_session: DBSession, session_id: str, user_phone: str) -> Session:
    """Close a session.

    Only the session owner can close the session.

    Args:
        db_session: Database session
        session_id: Session ID to close
        user_phone: Phone number of the user trying to close the session

    Returns:
        Closed session

    Raises:
        NoResultFound: If session is not found
        ValueError: If user is not the owner of the session
    """
    session = db_session.query(Session).filter(Session.id == session_id).one()
    user = get_user_by_phone_number(db_session, user_phone)
    
    if not user:
        raise NoResultFound(f"User with phone {user_phone} not found")
    
    # Check if user is the owner
    if session.owner_id != user.id:
        raise ValueError("Solo el creador de la sesión puede cerrarla")
    
    session.status = SessionStatus.CLOSED
    db_session.commit()
    return session


def create_session(db_session: DBSession, description: str, owner_number: str) -> Session:
    """Create a new session for a user.

    Args:
        db_session: Database session
        description: Session description
        owner_number: Owner phone number

    Returns:
        Created session
    """
    user = get_user_by_phone_number(db_session, owner_number)
    session = Session(description=description, owner_id=user.id, status=SessionStatus.ACTIVE)
    db_session.add(session)
    db_session.commit()
    return session


def get_session_by_id(db_session: DBSession, session_id: str) -> Session:
    """Get a session by its UUID.

    Args:
        db_session: Database session
        session_id: Session UUID as string

    Returns:
        Session object

    Raises:
        NoResultFound: If session is not found
        ValueError: If session_id is not a valid UUID
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid session ID format: {session_id}") from e

    session = db_session.query(Session).filter(Session.id == session_uuid).one()
    return session


def join_session(db_session: DBSession, session_id: str, user_phone: str) -> tuple[Session, bool]:
    """Join a user to an existing session.

    If the user has an active session, it will be closed first.
    Then the user will be added to the specified session.

    Args:
        db_session: Database session
        session_id: UUID of the session to join
        user_phone: Phone number of the user joining

    Returns:
        Tuple of (Session object that the user joined, whether user was already in session)

    Raises:
        NoResultFound: If session or user is not found
        ValueError: If session is closed or session_id is invalid
    """
    from app.database.models.session import session_users
    from sqlalchemy import select
    
    # Get user
    user = get_user_by_phone_number(db_session, user_phone)
    if not user:
        raise NoResultFound(f"User with phone {user_phone} not found")

    # Get target session
    target_session = get_session_by_id(db_session, session_id)

    # Check if target session is active
    if target_session.status != SessionStatus.ACTIVE:
        raise ValueError("No puedes unirte a una sesión cerrada")

    # Check if user is already in this session
    session_uuid = uuid.UUID(session_id)
    existing_membership = db_session.execute(
        select(session_users).where(
            session_users.c.session_id == session_uuid,
            session_users.c.user_id == user.id
        )
    ).first()

    if existing_membership:
        # User is already in the session
        return target_session, True

    # Close user's active session if exists and it's not the target session
    if has_active_session(db_session, user.id):
        try:
            active_session = get_active_session_by_user_id(db_session, user.id)
            # Only close if it's a different session
            if str(active_session.id) != session_id:
                active_session.status = SessionStatus.CLOSED
        except Exception:
            pass  # If there's an issue closing, continue

    # Add user to target session (many-to-many relationship)
    target_session.users.append(user)
    db_session.commit()
    db_session.refresh(target_session)

    return target_session, False
