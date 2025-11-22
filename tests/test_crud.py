"""Test CRUD operations for all models."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import (
    user_crud,
    session_crud,
    invoice_crud,
    item_crud,
    payment_crud,
)
from app.database.models.session import SessionStatus


@pytest.mark.asyncio
async def test_user_crud(db_session: AsyncSession) -> None:
    """Test User CRUD operations."""
    # Create
    user_data = {"name": "Test User", "phone_number": "+1234567899"}
    user = await user_crud.create(db_session, obj_in=user_data)
    assert user.id is not None
    assert user.name == "Test User"
    assert user.phone_number == "+1234567899"

    # Get by ID
    retrieved_user = await user_crud.get(db_session, id=user.id)
    assert retrieved_user is not None
    assert retrieved_user.name == "Test User"

    # Get by phone
    user_by_phone = await user_crud.get_by_phone(db_session, "+1234567899")
    assert user_by_phone is not None
    assert user_by_phone.id == user.id

    # Get by name
    users_by_name = await user_crud.get_by_name(db_session, "Test")
    assert len(users_by_name) > 0
    assert any(u.id == user.id for u in users_by_name)

    # Update
    updated_user = await user_crud.update(
        db_session, db_obj=user, obj_in={"name": "Updated User"}
    )
    assert updated_user.name == "Updated User"

    # Get multi
    users = await user_crud.get_multi(db_session, skip=0, limit=10)
    assert len(users) > 0

    # Delete
    deleted_user = await user_crud.delete(db_session, id=user.id)
    assert deleted_user is not None
    assert deleted_user.id == user.id

    # Verify deletion
    deleted_check = await user_crud.get(db_session, id=user.id)
    assert deleted_check is None


@pytest.mark.asyncio
async def test_session_crud(db_session: AsyncSession) -> None:
    """Test Session CRUD operations."""
    # Create a user first
    user_data = {"name": "Session Owner", "phone_number": "+1234567898"}
    owner = await user_crud.create(db_session, obj_in=user_data)

    # Create
    session_data = {
        "id": uuid.uuid4(),
        "description": "Test Session",
        "owner_id": owner.id,
        "status": SessionStatus.ACTIVE,
    }
    session = await session_crud.create(db_session, obj_in=session_data)
    assert session.id is not None
    assert session.description == "Test Session"
    assert session.status == SessionStatus.ACTIVE

    # Get by ID
    retrieved_session = await session_crud.get(db_session, id=session.id)
    assert retrieved_session is not None
    assert retrieved_session.description == "Test Session"

    # Get by owner
    sessions_by_owner = await session_crud.get_by_owner(db_session, owner.id)
    assert len(sessions_by_owner) > 0
    assert any(s.id == session.id for s in sessions_by_owner)

    # Get by status
    active_sessions = await session_crud.get_by_status(db_session, SessionStatus.ACTIVE)
    assert len(active_sessions) > 0

    # Get active sessions
    active = await session_crud.get_active_sessions(db_session)
    assert len(active) > 0

    # Update
    updated_session = await session_crud.update(
        db_session,
        db_obj=session,
        obj_in={"status": SessionStatus.CLOSED},
    )
    assert updated_session.status == SessionStatus.CLOSED

    # Delete
    deleted_session = await session_crud.delete(db_session, id=session.id)
    assert deleted_session is not None


@pytest.mark.asyncio
async def test_invoice_crud(db_session: AsyncSession) -> None:
    """Test Invoice CRUD operations."""
    # Create user and session first
    user_data = {"name": "Invoice Payer", "phone_number": "+1234567897"}
    payer = await user_crud.create(db_session, obj_in=user_data)

    session_data = {
        "id": uuid.uuid4(),
        "description": "Invoice Session",
        "owner_id": payer.id,
        "status": SessionStatus.ACTIVE,
    }
    session = await session_crud.create(db_session, obj_in=session_data)

    # Create
    invoice_data = {
        "description": "Test Invoice",
        "total": 100.00,
        "pending_amount": 50.00,
        "payer_id": payer.id,
        "session_id": session.id,
    }
    invoice = await invoice_crud.create(db_session, obj_in=invoice_data)
    assert invoice.id is not None
    assert invoice.total == 100.00
    assert invoice.pending_amount == 50.00

    # Get by ID
    retrieved_invoice = await invoice_crud.get(db_session, id=invoice.id)
    assert retrieved_invoice is not None

    # Get by payer
    invoices_by_payer = await invoice_crud.get_by_payer(db_session, payer.id)
    assert len(invoices_by_payer) > 0
    assert any(inv.id == invoice.id for inv in invoices_by_payer)

    # Get by session
    invoices_by_session = await invoice_crud.get_by_session(db_session, session.id)
    assert len(invoices_by_session) > 0
    assert any(inv.id == invoice.id for inv in invoices_by_session)

    # Get pending invoices
    pending = await invoice_crud.get_pending_invoices(db_session)
    assert len(pending) > 0

    # Update
    updated_invoice = await invoice_crud.update(
        db_session,
        db_obj=invoice,
        obj_in={"pending_amount": 25.00},
    )
    assert updated_invoice.pending_amount == 25.00

    # Delete
    deleted_invoice = await invoice_crud.delete(db_session, id=invoice.id)
    assert deleted_invoice is not None


@pytest.mark.asyncio
async def test_item_crud(db_session: AsyncSession) -> None:
    """Test Item CRUD operations."""
    # Create user, session, and invoice first
    user_data = {"name": "Item Debtor", "phone_number": "+1234567896"}
    debtor = await user_crud.create(db_session, obj_in=user_data)

    session_data = {
        "id": uuid.uuid4(),
        "description": "Item Session",
        "owner_id": debtor.id,
        "status": SessionStatus.ACTIVE,
    }
    session = await session_crud.create(db_session, obj_in=session_data)

    invoice_data = {
        "description": "Item Invoice",
        "total": 200.00,
        "pending_amount": 200.00,
        "payer_id": debtor.id,
        "session_id": session.id,
    }
    invoice = await invoice_crud.create(db_session, obj_in=invoice_data)

    # Create
    item_data = {
        "invoice_id": invoice.id,
        "debtor_id": debtor.id,
        "unit_price": 50.00,
        "paid_amount": 0.00,
        "tip": 0.15,
        "total": 57.50,
        "is_paid": False,
    }
    item = await item_crud.create(db_session, obj_in=item_data)
    assert item.id is not None
    assert item.unit_price == 50.00
    assert item.total == 57.50
    assert item.is_paid is False

    # Get by ID
    retrieved_item = await item_crud.get(db_session, id=item.id)
    assert retrieved_item is not None

    # Get by invoice
    items_by_invoice = await item_crud.get_by_invoice(db_session, invoice.id)
    assert len(items_by_invoice) > 0
    assert any(i.id == item.id for i in items_by_invoice)

    # Get by debtor
    items_by_debtor = await item_crud.get_by_debtor(db_session, debtor.id)
    assert len(items_by_debtor) > 0
    assert any(i.id == item.id for i in items_by_debtor)

    # Get unpaid items
    unpaid = await item_crud.get_unpaid_items(db_session)
    assert len(unpaid) > 0

    # Update
    updated_item = await item_crud.update(
        db_session,
        db_obj=item,
        obj_in={"is_paid": True, "paid_amount": 57.50},
    )
    assert updated_item.is_paid is True
    assert updated_item.paid_amount == 57.50

    # Delete
    deleted_item = await item_crud.delete(db_session, id=item.id)
    assert deleted_item is not None


@pytest.mark.asyncio
async def test_payment_crud(db_session: AsyncSession) -> None:
    """Test Payment CRUD operations."""
    # Create users first
    payer_data = {"name": "Payment Payer", "phone_number": "+1234567895"}
    payer = await user_crud.create(db_session, obj_in=payer_data)

    receiver_data = {"name": "Payment Receiver", "phone_number": "+1234567894"}
    receiver = await user_crud.create(db_session, obj_in=receiver_data)

    # Create
    payment_data = {
        "payer_id": payer.id,
        "receiver_id": receiver.id,
        "amount": 75.50,
    }
    payment = await payment_crud.create(db_session, obj_in=payment_data)
    assert payment.id is not None
    assert payment.amount == 75.50
    assert payment.payer_id == payer.id
    assert payment.receiver_id == receiver.id

    # Get by ID
    retrieved_payment = await payment_crud.get(db_session, id=payment.id)
    assert retrieved_payment is not None

    # Get by payer
    payments_by_payer = await payment_crud.get_by_payer(db_session, payer.id)
    assert len(payments_by_payer) > 0
    assert any(p.id == payment.id for p in payments_by_payer)

    # Get by receiver
    payments_by_receiver = await payment_crud.get_by_receiver(db_session, receiver.id)
    assert len(payments_by_receiver) > 0
    assert any(p.id == payment.id for p in payments_by_receiver)

    # Get between users
    payments_between = await payment_crud.get_between_users(
        db_session, payer.id, receiver.id
    )
    assert len(payments_between) > 0
    assert any(p.id == payment.id for p in payments_between)

    # Update
    updated_payment = await payment_crud.update(
        db_session,
        db_obj=payment,
        obj_in={"amount": 100.00},
    )
    assert updated_payment.amount == 100.00

    # Delete
    deleted_payment = await payment_crud.delete(db_session, id=payment.id)
    assert deleted_payment is not None


@pytest.mark.asyncio
async def test_relationships(db_session: AsyncSession) -> None:
    """Test that relationships work correctly."""
    # Create users
    user1_data = {"name": "User 1", "phone_number": "+1111111111"}
    user1 = await user_crud.create(db_session, obj_in=user1_data)

    user2_data = {"name": "User 2", "phone_number": "+2222222222"}
    user2 = await user_crud.create(db_session, obj_in=user2_data)

    # Create session with owner
    session_data = {
        "id": uuid.uuid4(),
        "description": "Relationship Test Session",
        "owner_id": user1.id,
        "status": SessionStatus.ACTIVE,
    }
    session = await session_crud.create(db_session, obj_in=session_data)

    # Add users to session using the association table directly
    from app.database.models.session import session_users
    from sqlalchemy import insert
    
    # Insert into association table
    await db_session.execute(
        insert(session_users).values([
            {"session_id": session.id, "user_id": user1.id},
            {"session_id": session.id, "user_id": user2.id},
        ])
    )
    await db_session.commit()
    
    # Eagerly load the users relationship
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.database.models.session import Session as SessionModel
    result = await db_session.execute(
        select(SessionModel)
        .options(selectinload(SessionModel.users))
        .where(SessionModel.id == session.id)
    )
    session_with_users = result.scalar_one()

    # Verify relationships
    assert session_with_users.owner_id == user1.id
    assert len(session_with_users.users) == 2

    # Create invoice
    invoice_data = {
        "description": "Relationship Test Invoice",
        "total": 150.00,
        "pending_amount": 150.00,
        "payer_id": user1.id,
        "session_id": session.id,
    }
    invoice = await invoice_crud.create(db_session, obj_in=invoice_data)

    # Verify invoice relationships
    await db_session.refresh(invoice)
    assert invoice.payer_id == user1.id
    assert invoice.session_id == session.id
    
    # Refresh session to get updated invoice
    await db_session.refresh(session_with_users)

    # Create item
    item_data = {
        "invoice_id": invoice.id,
        "debtor_id": user2.id,
        "unit_price": 75.00,
        "paid_amount": 0.00,
        "tip": 0.10,
        "total": 82.50,
        "is_paid": False,
    }
    item = await item_crud.create(db_session, obj_in=item_data)

    # Verify item relationships
    await db_session.refresh(item)
    assert item.invoice_id == invoice.id
    assert item.debtor_id == user2.id

    # Create payment
    payment_data = {
        "payer_id": user2.id,
        "receiver_id": user1.id,
        "amount": 82.50,
    }
    payment = await payment_crud.create(db_session, obj_in=payment_data)

    # Link payment to item
    updated_item = await item_crud.update(
        db_session, db_obj=item, obj_in={"payment_id": payment.id, "is_paid": True}
    )

    # Verify payment relationships
    await db_session.refresh(payment)
    assert payment.payer_id == user2.id
    assert payment.receiver_id == user1.id
    assert updated_item.payment_id == payment.id
    assert updated_item.is_paid is True

