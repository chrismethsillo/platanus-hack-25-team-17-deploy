"""add unique constraint to users phone_number

Revision ID: e19835d69ac8
Revises: 899d11cd630f
Create Date: 2025-11-22 18:10:56.402409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e19835d69ac8'
down_revision: Union[str, Sequence[str], None] = '899d11cd630f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove duplicates first (keep the first occurrence)
    op.execute("""
        DELETE FROM users a USING users b
        WHERE a.id > b.id AND a.phone_number = b.phone_number;
    """)
    
    # Add unique constraint to phone_number
    op.create_unique_constraint('uq_users_phone_number', 'users', ['phone_number'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove unique constraint
    op.drop_constraint('uq_users_phone_number', 'users', type_='unique')
