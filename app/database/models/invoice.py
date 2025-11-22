"""Invoice model definition."""

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Invoice(Base):
    """Invoice model.

    Represents an invoice that tracks the total amount, pending amount,
    and which user paid for it.

    Attributes:
        id: Primary key
        description: Description of the invoice
        total: Total amount of the invoice
        pending_amount: Amount still pending to be paid
        payer_id: ID of the user who paid the invoice
        payer: User who paid this invoice
        items: Items associated with this invoice
    """

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    pending_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)

    # Relationships
    payer: Mapped["User"] = relationship("User", back_populates="invoices", foreign_keys=[payer_id])

    items: Mapped[list["Item"]] = relationship("Item", back_populates="invoice")

    session: Mapped["Session"] = relationship("Session", back_populates="invoices", foreign_keys=[session_id])
