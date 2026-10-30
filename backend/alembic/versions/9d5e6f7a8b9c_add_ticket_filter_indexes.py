"""add ticket filter indexes

Revision ID: 9d5e6f7a8b9c
Revises: 8c4f1a2b3d4e
Create Date: 2026-10-30 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d5e6f7a8b9c"
down_revision: Union[str, Sequence[str], None] = "8c4f1a2b3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEXES = {
    "ix_tickets_ticket_type": ["ticket_type"],
    "ix_tickets_status": ["status"],
    "ix_tickets_area_id": ["area_id"],
    "ix_tickets_priority": ["priority"],
}


def upgrade() -> None:
    bind = op.get_bind()
    existing = {
        index["name"] for index in sa.inspect(bind).get_indexes("tickets")
    }
    for name, columns in _INDEXES.items():
        if name not in existing:
            op.create_index(name, "tickets", columns)


def downgrade() -> None:
    bind = op.get_bind()
    existing = {
        index["name"] for index in sa.inspect(bind).get_indexes("tickets")
    }
    for name in ("ix_tickets_status", "ix_tickets_priority"):
        if name in existing:
            op.drop_index(name, table_name="tickets")
