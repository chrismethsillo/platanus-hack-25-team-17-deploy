from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.payment_method import PaymentMethod
from sqlalchemy import select


async def get_user_payment_methods(db_session: AsyncSession, user_id: int) -> list[PaymentMethod]:
    result = await db_session.execute(select(PaymentMethod).where(PaymentMethod.id_user == user_id))
    return result.scalars().all()


async def create_payment_method(
    db_session: AsyncSession, user_id: int, name: str, description: str | None = None
) -> PaymentMethod:
    """Create a new payment method for a user.
    
    Args:
        db_session: Database session
        user_id: ID of the user
        name: Name of the payment method (e.g., "Transferencia", "Yape", "Plin")
        description: Description/details of the payment method (e.g., account number, phone number)
    
    Returns:
        Created PaymentMethod object
    """
    payment_method = PaymentMethod(id_user=user_id, name=name, description=description)
    db_session.add(payment_method)
    await db_session.commit()
    await db_session.refresh(payment_method)
    return payment_method
