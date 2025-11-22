"""Session endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import session_crud
from app.database.models.session import SessionStatus
from app.routers.deps import get_db

router = APIRouter()


@router.get("/")
async def get_sessions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get all sessions with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of sessions
    """
    sessions = await session_crud.get_multi(db, skip=skip, limit=limit)
    return sessions


@router.get("/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a session by ID.

    Args:
        session_id: Session UUID
        db: Database session

    Returns:
        Session instance

    Raises:
        HTTPException: If session not found
    """
    session = await session_crud.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/owner/{owner_id}")
async def get_sessions_by_owner(
    owner_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get sessions by owner ID.

    Args:
        owner_id: Owner's user ID
        db: Database session

    Returns:
        List of sessions owned by the user
    """
    sessions = await session_crud.get_by_owner(db, owner_id)
    return sessions


@router.get("/status/{status}")
async def get_sessions_by_status(
    status: SessionStatus,
    db: AsyncSession = Depends(get_db),
):
    """Get sessions by status.

    Args:
        status: Session status (active or closed)
        db: Database session

    Returns:
        List of sessions with the specified status
    """
    sessions = await session_crud.get_by_status(db, status)
    return sessions


@router.get("/active/all")
async def get_active_sessions(
    db: AsyncSession = Depends(get_db),
):
    """Get all active sessions.

    Args:
        db: Database session

    Returns:
        List of active sessions
    """
    sessions = await session_crud.get_active_sessions(db)
    return sessions

