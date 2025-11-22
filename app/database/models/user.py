"""User model definition."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class User(Base):
    """User model.

    Represents a user in the system with basic contact information.

    Attributes:
        id: Primary key
        name: User's full name
        phone_number: User's phone number
        invoices: Invoices paid by this user
        debtor_items: Items where this user is the debtor
        payments_made: Payments made by this user
        payments_received: Payments received by this user
        sessions: Sessions associated with this user
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="payer", foreign_keys="Invoice.payer_id")

    debtor_items: Mapped[list["Item"]] = relationship("Item", back_populates="debtor", foreign_keys="Item.debtor_id")

    payments_made: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="payer", foreign_keys="Payment.payer_id"
    )

    payments_received: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="receiver", foreign_keys="Payment.receiver_id"
    )

    sessions: Mapped[list["Session"]] = relationship(secondary="session_users", back_populates="users")
