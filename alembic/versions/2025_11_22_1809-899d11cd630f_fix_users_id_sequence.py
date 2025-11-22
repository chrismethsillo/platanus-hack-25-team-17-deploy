"""fix users id sequence

Revision ID: 899d11cd630f
Revises: 83a5ba861ffb
Create Date: 2025-11-22 18:09:56.351701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '899d11cd630f'
down_revision: Union[str, Sequence[str], None] = '83a5ba861ffb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Reset the users table ID sequence to the correct value
    # This fixes the issue where the sequence gets out of sync
    op.execute("""
        SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1), true);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # No need to downgrade, this is a fix operation
    pass
