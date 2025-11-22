"""Session model definition."""

from sqlalchemy import String, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base

# Association table for many-to-many relationship between Session and User
session_users = Table(
    "session_users",
    Base.metadata,
    Column("session_id", ForeignKey("sessions.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class SessionStatus(Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class Session(Base):
    """Session model.

    Represents a session with multiple users participating.

    Attributes:
        id: Primary key
        description: Description of the session
        users: Users participating in this session (many-to-many)
    """

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(SessionStatus, name="session_status", nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship(secondary=session_users, back_populates="sessions")
    owner: Mapped["User"] = relationship("User", back_populates="sessions", foreign_keys=[owner_id])
