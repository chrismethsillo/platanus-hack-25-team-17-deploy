from sqlalchemy.orm import Session
from app.database.models.user import User


def get_user_by_phone_number(db_session: Session, phone_number: str) -> User | None:
    return db_session.query(User).filter(User.phone_number == phone_number).first()
