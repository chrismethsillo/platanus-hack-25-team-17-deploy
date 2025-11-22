"""Item model definition."""

from sqlalchemy import Numeric, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database.database import Base


class Item(Base):
    """Item model.

    Represents an item within an invoice. Has a debtor (user), unit price,
    optional tip, and tracks payment status.

    Attributes:
        id: Primary key
        invoice_id: ID of the associated invoice (N to 1 relationship)
        debtor_id: ID of the user who is the debtor for this item
        unit_price: Base price of the item
        paid_amount: Amount paid so far (for partial payments)
        tip: Tip percentage (as decimal, e.g., 0.10 for 10%)
        total: Total amount including tip (unit_price + tip_amount)
        is_paid: Whether the item has been fully paid
        payment_id: ID of the payment associated with this item (optional)
        invoice: Associated invoice
        debtor: User who is the debtor
        payment: Associated payment
    """

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    debtor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    tip: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payments.id"), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")

    debtor: Mapped["User"] = relationship("User", back_populates="debtor_items", foreign_keys=[debtor_id])

    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="items")
