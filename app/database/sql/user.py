from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database.models.user import User
import logging


def get_user_by_phone_number(db_session: Session, phone_number: str) -> User | None:
    """Get a user by their phone number.

    Args:
        db_session: Database session
        phone_number: Phone number to search for

    Returns:
        User object if found, None otherwise
    """
    logging.info(f"Getting user by phone number: {phone_number}")
    try:
        user = db_session.query(User).filter(User.phone_number == phone_number).one_or_none()
        logging.info(f"User: {user}")
        return user
    except Exception as e:
        logging.error(f"Error getting user by phone number: {e}", exc_info=True)
        return None


def create_user(db_session: Session, phone_number: str, name: str) -> User:
    """Create a new user.

    Args:
        db_session: Database session
        phone_number: User's phone number
        name: User's name

    Returns:
        Created User object

    Raises:
        IntegrityError: If user with same phone number already exists
    """
    try:
        user = User(phone_number=phone_number, name=name)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        logging.info(f"Created new user: {user.id} - {phone_number}")
        return user
    except IntegrityError as e:
        db_session.rollback()
        logging.warning(f"User with phone {phone_number} already exists, fetching existing user")
        # If user already exists, fetch and return it
        existing_user = get_user_by_phone_number(db_session, phone_number)
        if existing_user:
            return existing_user
        raise e  # Re-raise if we couldn't find the existing user
