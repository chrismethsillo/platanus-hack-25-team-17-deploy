"""Item endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import item_crud
from app.routers.deps import get_db

router = APIRouter()


@router.get("/")
async def get_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get all items with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of items
    """
    items = await item_crud.get_multi(db, skip=skip, limit=limit)
    return items


@router.get("/{item_id}")
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an item by ID.

    Args:
        item_id: Item ID
        db: Database session

    Returns:
        Item instance

    Raises:
        HTTPException: If item not found
    """
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/invoice/{invoice_id}")
async def get_items_by_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get items by invoice ID.

    Args:
        invoice_id: Invoice ID
        db: Database session

    Returns:
        List of items for the invoice
    """
    items = await item_crud.get_by_invoice(db, invoice_id)
    return items


@router.get("/debtor/{debtor_id}")
async def get_items_by_debtor(
    debtor_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get items by debtor ID.

    Args:
        debtor_id: Debtor's user ID
        db: Database session

    Returns:
        List of items where the user is the debtor
    """
    items = await item_crud.get_by_debtor(db, debtor_id)
    return items


@router.get("/unpaid/all")
async def get_unpaid_items(
    db: AsyncSession = Depends(get_db),
):
    """Get all unpaid items.

    Args:
        db: Database session

    Returns:
        List of unpaid items
    """
    items = await item_crud.get_unpaid_items(db)
    return items


@router.get("/payment/{payment_id}")
async def get_items_by_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get items by payment ID.

    Args:
        payment_id: Payment ID
        db: Database session

    Returns:
        List of items associated with the payment
    """
    items = await item_crud.get_by_payment(db, payment_id)
    return items

