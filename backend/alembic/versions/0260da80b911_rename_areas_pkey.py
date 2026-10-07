"""rename_areas_pkey

Revision ID: <auto>
Revises: 152499059c9e
Create Date: <auto>
"""
from typing import Sequence, Union

from alembic import op


revision: str = "<auto>"
down_revision: Union[str, Sequence[str], None] = "152499059c9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER INDEX departments_pkey RENAME TO areas_pkey")


def downgrade() -> None:
    op.execute("ALTER INDEX areas_pkey RENAME TO departments_pkey")