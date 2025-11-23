"""merge remaining heads

Revision ID: bb6b73e5fa51
Revises: f9f9745cadf9, c9d7d3b42539
Create Date: 2025-11-23 01:08:06.257806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb6b73e5fa51'
down_revision: Union[str, Sequence[str], None] = ('f9f9745cadf9', 'c9d7d3b42539')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
