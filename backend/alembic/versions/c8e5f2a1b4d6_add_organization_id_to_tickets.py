"""add organization_id to tickets

Revision ID: c8e5f2a1b4d6
Revises: b7d4e9f1a2c3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c8e5f2a1b4d6"
down_revision: Union[str, Sequence[str], None] = "b7d4e9f1a2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_tickets_organization_id",
        "tickets",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tickets_organization_id", table_name="tickets")
    op.drop_column("tickets", "organization_id")
