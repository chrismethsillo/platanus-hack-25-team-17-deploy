"""merge_heads

Revision ID: 9a951e74a26f
Revises: f9f9745cadf9, c9d7d3b42539
Create Date: 2025-11-23 01:03:52.603034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a951e74a26f'
down_revision: Union[str, Sequence[str], None] = ('f9f9745cadf9', 'c9d7d3b42539')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
