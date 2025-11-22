"""Payment endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import payment_crud
from app.routers.deps import get_db

router = APIRouter()


@router.get("/")
async def get_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get all payments with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of payments
    """
    payments = await payment_crud.get_multi(db, skip=skip, limit=limit)
    return payments


@router.get("/{payment_id}")
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a payment by ID.

    Args:
        payment_id: Payment ID
        db: Database session

    Returns:
        Payment instance

    Raises:
        HTTPException: If payment not found
    """
    payment = await payment_crud.get(db, id=payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/payer/{payer_id}")
async def get_payments_by_payer(
    payer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get payments by payer ID.

    Args:
        payer_id: Payer's user ID
        db: Database session

    Returns:
        List of payments made by the user
    """
    payments = await payment_crud.get_by_payer(db, payer_id)
    return payments


@router.get("/receiver/{receiver_id}")
async def get_payments_by_receiver(
    receiver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get payments by receiver ID.

    Args:
        receiver_id: Receiver's user ID
        db: Database session

    Returns:
        List of payments received by the user
    """
    payments = await payment_crud.get_by_receiver(db, receiver_id)
    return payments


@router.get("/between/{payer_id}/{receiver_id}")
async def get_payments_between_users(
    payer_id: int,
    receiver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get payments between two users.

    Args:
        payer_id: Payer's user ID
        receiver_id: Receiver's user ID
        db: Database session

    Returns:
        List of payments between the two users
    """
    payments = await payment_crud.get_between_users(db, payer_id, receiver_id)
    return payments

