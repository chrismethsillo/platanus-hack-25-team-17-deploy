"""Payment method model definition."""

from app.database.database import Base
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.user import User


class PaymentMethod(Base):
    """Payment method model.

    Represents a payment method for a user.

    Attributes:
        id: Primary key
        name: Name of the payment method
        description: Description of the payment method
        id_user: ID of the user who has this payment method
        user: User who has this payment method
    """

    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[id_user])
