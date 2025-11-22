"""CRUD operations package.

This package contains CRUD (Create, Read, Update, Delete) operations
for database models.

Example:
    ```python
    from app.database.crud import user_crud

    # In a route
    @router.get("/users/{user_id}")
    async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
        return await user_crud.get(db, id=user_id)
    ```
"""

from app.database.crud.user import user_crud, CRUDUser
from app.database.crud.session import session_crud, CRUDSession
from app.database.crud.invoice import invoice_crud, CRUDInvoice
from app.database.crud.item import item_crud, CRUDItem
from app.database.crud.payment import payment_crud, CRUDPayment

__all__ = [
    "user_crud",
    "CRUDUser",
    "session_crud",
    "CRUDSession",
    "invoice_crud",
    "CRUDInvoice",
    "item_crud",
    "CRUDItem",
    "payment_crud",
    "CRUDPayment",
]
