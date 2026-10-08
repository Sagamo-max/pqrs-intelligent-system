"""rename_areas_pkey

Revision ID: 0260da80b911
Revises: 152499059c9e
Create Date: 2026-10-08 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "0260da80b911"
down_revision: Union[str, Sequence[str], None] = "152499059c9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER INDEX departments_pkey RENAME TO areas_pkey")


def downgrade() -> None:
    op.execute("ALTER INDEX areas_pkey RENAME TO departments_pkey")