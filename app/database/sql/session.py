from sqlalchemy.orm import Session
from app.database.models.session import Session, SessionStatus


def get_active_session_by_user_id(db_session: Session, user_id: int) -> Session | None:
    return (
        db_session.query(Session)
        .filter(Session.owner_id == user_id)
        .filter(Session.status == SessionStatus.ACTIVE)
        .one()
    )
