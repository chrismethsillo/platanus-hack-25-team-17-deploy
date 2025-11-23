"""merge all heads

Revision ID: 967585cee6ef
Revises: 9a951e74a26f, bb6b73e5fa51
Create Date: 2025-11-23 01:21:49.778880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '967585cee6ef'
down_revision: Union[str, Sequence[str], None] = ('9a951e74a26f', 'bb6b73e5fa51')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
