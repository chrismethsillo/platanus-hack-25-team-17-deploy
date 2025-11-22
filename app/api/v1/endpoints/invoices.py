"""Invoice endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import invoice_crud
from app.routers.deps import get_db

router = APIRouter()


@router.get("/")
async def get_invoices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get all invoices with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of invoices
    """
    invoices = await invoice_crud.get_multi(db, skip=skip, limit=limit)
    return invoices


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an invoice by ID.

    Args:
        invoice_id: Invoice ID
        db: Database session

    Returns:
        Invoice instance

    Raises:
        HTTPException: If invoice not found
    """
    invoice = await invoice_crud.get(db, id=invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/payer/{payer_id}")
async def get_invoices_by_payer(
    payer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get invoices by payer ID.

    Args:
        payer_id: Payer's user ID
        db: Database session

    Returns:
        List of invoices paid by the user
    """
    invoices = await invoice_crud.get_by_payer(db, payer_id)
    return invoices


@router.get("/session/{session_id}")
async def get_invoices_by_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get invoices by session ID.

    Args:
        session_id: Session UUID
        db: Database session

    Returns:
        List of invoices for the session
    """
    invoices = await invoice_crud.get_by_session(db, session_id)
    return invoices


@router.get("/pending/all")
async def get_pending_invoices(
    db: AsyncSession = Depends(get_db),
):
    """Get all invoices with pending amounts.

    Args:
        db: Database session

    Returns:
        List of invoices with pending_amount > 0
    """
    invoices = await invoice_crud.get_pending_invoices(db)
    return invoices

