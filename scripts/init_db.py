"""Initialize database with example data.

This script populates the database with sample data for development and testing.
Run it after migrations have been applied.

Usage:
    python scripts/init_db.py
    # Or with poetry
    poetry run python scripts/init_db.py
"""

import asyncio
import uuid

from app.config import settings
from app.database import db_manager
from app.database.crud import (
    user_crud,
    session_crud,
    invoice_crud,
    item_crud,
    payment_crud,
)
from app.database.models.session import SessionStatus


async def init_db() -> None:
    """Initialize database with example data."""
    print("Connecting to database...")
    await db_manager.connect()

    try:
        session_maker = db_manager.sessionmaker()
        async with session_maker() as db:
            print("Creating example users...")
            # Create users
            users_data = [
                {"name": "Alice Johnson", "phone_number": "+1234567890"},
                {"name": "Bob Smith", "phone_number": "+1234567891"},
                {"name": "Charlie Brown", "phone_number": "+1234567892"},
                {"name": "Diana Prince", "phone_number": "+1234567893"},
                {"name": "Eve Wilson", "phone_number": "+1234567894"},
            ]

            users = []
            for user_data in users_data:
                # Check if user already exists
                existing_user = await user_crud.get_by_phone(db, user_data["phone_number"])
                if existing_user:
                    print(f"  User {user_data['name']} already exists, skipping...")
                    users.append(existing_user)
                else:
                    user = await user_crud.create(db, obj_in=user_data)
                    users.append(user)
                    print(f"  Created user: {user.name} (ID: {user.id})")

            alice, bob, charlie, diana, eve = users

            print("\nCreating example sessions...")
            # Create sessions
            session1_data = {
                "id": uuid.uuid4(),
                "description": "Dinner at Italian Restaurant",
                "owner_id": alice.id,
                "status": SessionStatus.ACTIVE,
            }
            session1 = await session_crud.create(db, obj_in=session1_data)
            # Add users to session
            session1.users = [alice, bob, charlie]
            await db.commit()
            await db.refresh(session1)
            print(f"  Created session: {session1.description} (ID: {session1.id})")

            session2_data = {
                "id": uuid.uuid4(),
                "description": "Weekend Trip Expenses",
                "owner_id": bob.id,
                "status": SessionStatus.ACTIVE,
            }
            session2 = await session_crud.create(db, obj_in=session2_data)
            session2.users = [bob, charlie, diana, eve]
            await db.commit()
            await db.refresh(session2)
            print(f"  Created session: {session2.description} (ID: {session2.id})")

            session3_data = {
                "id": uuid.uuid4(),
                "description": "Coffee Meeting",
                "owner_id": charlie.id,
                "status": SessionStatus.CLOSED,
            }
            session3 = await session_crud.create(db, obj_in=session3_data)
            session3.users = [charlie, diana]
            await db.commit()
            await db.refresh(session3)
            print(f"  Created session: {session3.description} (ID: {session3.id})")

            print("\nCreating example invoices...")
            # Create invoices for session1
            invoice1_data = {
                "description": "Dinner bill - Italian Restaurant",
                "total": 150.00,
                "pending_amount": 50.00,
                "payer_id": alice.id,
                "session_id": session1.id,
            }
            invoice1 = await invoice_crud.create(db, obj_in=invoice1_data)
            print(f"  Created invoice: {invoice1.description} (Total: ${invoice1.total})")

            invoice2_data = {
                "description": "Drinks and appetizers",
                "total": 45.00,
                "pending_amount": 45.00,
                "payer_id": bob.id,
                "session_id": session1.id,
            }
            invoice2 = await invoice_crud.create(db, obj_in=invoice2_data)
            print(f"  Created invoice: {invoice2.description} (Total: ${invoice2.total})")

            # Create invoice for session2
            invoice3_data = {
                "description": "Hotel booking",
                "total": 300.00,
                "pending_amount": 150.00,
                "payer_id": bob.id,
                "session_id": session2.id,
            }
            invoice3 = await invoice_crud.create(db, obj_in=invoice3_data)
            print(f"  Created invoice: {invoice3.description} (Total: ${invoice3.total})")

            print("\nCreating example items...")
            # Create items for invoice1
            items_data = [
                {
                    "invoice_id": invoice1.id,
                    "debtor_id": bob.id,
                    "unit_price": 50.00,
                    "paid_amount": 50.00,
                    "tip": 0.15,
                    "total": 57.50,
                    "is_paid": True,
                },
                {
                    "invoice_id": invoice1.id,
                    "debtor_id": charlie.id,
                    "unit_price": 50.00,
                    "paid_amount": 0.00,
                    "tip": 0.15,
                    "total": 57.50,
                    "is_paid": False,
                },
                {
                    "invoice_id": invoice1.id,
                    "debtor_id": alice.id,
                    "unit_price": 50.00,
                    "paid_amount": 50.00,
                    "tip": 0.15,
                    "total": 57.50,
                    "is_paid": True,
                },
                {
                    "invoice_id": invoice2.id,
                    "debtor_id": charlie.id,
                    "unit_price": 15.00,
                    "paid_amount": 0.00,
                    "tip": 0.20,
                    "total": 18.00,
                    "is_paid": False,
                },
                {
                    "invoice_id": invoice2.id,
                    "debtor_id": bob.id,
                    "unit_price": 15.00,
                    "paid_amount": 0.00,
                    "tip": 0.20,
                    "total": 18.00,
                    "is_paid": False,
                },
                {
                    "invoice_id": invoice2.id,
                    "debtor_id": alice.id,
                    "unit_price": 15.00,
                    "paid_amount": 0.00,
                    "tip": 0.20,
                    "total": 18.00,
                    "is_paid": False,
                },
                {
                    "invoice_id": invoice3.id,
                    "debtor_id": charlie.id,
                    "unit_price": 75.00,
                    "paid_amount": 0.00,
                    "tip": 0.0,
                    "total": 75.00,
                    "is_paid": False,
                },
                {
                    "invoice_id": invoice3.id,
                    "debtor_id": diana.id,
                    "unit_price": 75.00,
                    "paid_amount": 75.00,
                    "tip": 0.0,
                    "total": 75.00,
                    "is_paid": True,
                },
                {
                    "invoice_id": invoice3.id,
                    "debtor_id": eve.id,
                    "unit_price": 75.00,
                    "paid_amount": 0.00,
                    "tip": 0.0,
                    "total": 75.00,
                    "is_paid": False,
                },
                {
                    "invoice_id": invoice3.id,
                    "debtor_id": bob.id,
                    "unit_price": 75.00,
                    "paid_amount": 75.00,
                    "tip": 0.0,
                    "total": 75.00,
                    "is_paid": True,
                },
            ]

            items = []
            for item_data in items_data:
                item = await item_crud.create(db, obj_in=item_data)
                items.append(item)
                print(
                    f"  Created item: ${item.unit_price} for {item.debtor.name} "
                    f"(Paid: {item.is_paid})"
                )

            print("\nCreating example payments...")
            # Create payments
            payment1_data = {
                "payer_id": bob.id,
                "receiver_id": alice.id,
                "amount": 57.50,
            }
            payment1 = await payment_crud.create(db, obj_in=payment1_data)
            # Link payment to items
            bob_item = next((i for i in items if i.debtor_id == bob.id and i.invoice_id == invoice1.id), None)
            if bob_item:
                await item_crud.update(db, db_obj=bob_item, obj_in={"payment_id": payment1.id})
            print(f"  Created payment: ${payment1.amount} from {payment1.payer.name} to {payment1.receiver.name}")

            payment2_data = {
                "payer_id": diana.id,
                "receiver_id": bob.id,
                "amount": 75.00,
            }
            payment2 = await payment_crud.create(db, obj_in=payment2_data)
            diana_item = next((i for i in items if i.debtor_id == diana.id and i.invoice_id == invoice3.id), None)
            if diana_item:
                await item_crud.update(db, db_obj=diana_item, obj_in={"payment_id": payment2.id})
            print(f"  Created payment: ${payment2.amount} from {payment2.payer.name} to {payment2.receiver.name}")

            payment3_data = {
                "payer_id": bob.id,
                "receiver_id": bob.id,
                "amount": 75.00,
            }
            payment3 = await payment_crud.create(db, obj_in=payment3_data)
            bob_hotel_item = next((i for i in items if i.debtor_id == bob.id and i.invoice_id == invoice3.id), None)
            if bob_hotel_item:
                await item_crud.update(db, db_obj=bob_hotel_item, obj_in={"payment_id": payment3.id})
            print(f"  Created payment: ${payment3.amount} from {payment3.payer.name} to {payment3.receiver.name}")

            await db.commit()
            print("\n✅ Database initialized successfully!")
            print(f"\nSummary:")
            print(f"  - Users: {len(users)}")
            print(f"  - Sessions: 3")
            print(f"  - Invoices: 3")
            print(f"  - Items: {len(items)}")
            print(f"  - Payments: 3")

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        raise
    finally:
        print("\nDisconnecting from database...")
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(init_db())

