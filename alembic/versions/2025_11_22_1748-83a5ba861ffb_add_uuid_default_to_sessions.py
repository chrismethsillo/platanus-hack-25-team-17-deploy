"""add uuid default to sessions

Revision ID: 83a5ba861ffb
Revises: ad03aeb0d40a
Create Date: 2025-11-22 17:48:30.422513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83a5ba861ffb'
down_revision: Union[str, Sequence[str], None] = 'ad03aeb0d40a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add UUID default generation using PostgreSQL's gen_random_uuid() function
    op.execute("ALTER TABLE sessions ALTER COLUMN id SET DEFAULT gen_random_uuid()")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove UUID default generation
    op.execute("ALTER TABLE sessions ALTER COLUMN id DROP DEFAULT")
