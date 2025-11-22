"""User endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import user_crud
from app.routers.deps import get_db

router = APIRouter()


@router.get("/")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get all users with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of users
    """
    users = await user_crud.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a user by ID.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        User instance

    Raises:
        HTTPException: If user not found
    """
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/phone/{phone_number}")
async def get_user_by_phone(
    phone_number: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a user by phone number.

    Args:
        phone_number: User's phone number
        db: Database session

    Returns:
        User instance or None

    Raises:
        HTTPException: If user not found
    """
    user = await user_crud.get_by_phone(db, phone_number)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/search/name/{name}")
async def get_users_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get users by name (partial match).

    Args:
        name: User's name (partial match)
        db: Database session

    Returns:
        List of users matching the name
    """
    users = await user_crud.get_by_name(db, name)
    return users

