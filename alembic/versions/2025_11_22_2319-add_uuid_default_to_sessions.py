"""add uuid default to sessions

Revision ID: a1b2c3d4e5f6
Revises: be81b259ef2e
Create Date: 2025-11-22 23:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9f9745cadf9'
down_revision: Union[str, Sequence[str], None] = 'be81b259ef2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add server_default to generate UUID automatically
    op.alter_column('sessions', 'id',
                   existing_type=sa.UUID(),
                   server_default=sa.text('gen_random_uuid()'),
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove server_default
    op.alter_column('sessions', 'id',
                   existing_type=sa.UUID(),
                   server_default=None,
                   existing_nullable=False)

