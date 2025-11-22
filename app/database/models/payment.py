"""Payment model definition."""

from sqlalchemy import Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.database.database import Base


class Payment(Base):
    """Payment model.

    Represents a payment transaction between two users.

    Attributes:
        id: Primary key
        payer_id: ID of the user who made the payment
        receiver_id: ID of the user who received the payment
        amount: Amount of the payment
        payer: User who made the payment
        receiver: User who received the payment
        items: Items associated with this payment
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    payer: Mapped["User"] = relationship("User", back_populates="payments_made", foreign_keys=[payer_id])

    receiver: Mapped["User"] = relationship("User", back_populates="payments_received", foreign_keys=[receiver_id])

    items: Mapped[list["Item"]] = relationship("Item", back_populates="payment")
