"""merge heads

Revision ID: 9d7a31c90a42
Revises: ccc921b28649, create_drift_stats
Create Date: 2025-08-28 16:32:59.275325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d7a31c90a42'
down_revision: Union[str, Sequence[str], None] = ('ccc921b28649', 'create_drift_stats')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
