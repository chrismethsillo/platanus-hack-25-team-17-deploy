"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    invoices,
    items,
    payments,
    sessions,
    users,
)

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

