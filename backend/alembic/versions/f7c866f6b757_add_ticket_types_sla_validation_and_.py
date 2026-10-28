"""add ticket types, sla validation and nullable due_date

Revision ID: f7c866f6b757
Revises: fc9b7aa1bd27
Create Date: 2026-10-28 15:33:55.380712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f7c866f6b757'
down_revision: Union[str, Sequence[str], None] = 'fc9b7aa1bd27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) ALTER TYPE fuera de transacción (Postgres no lo permite dentro)
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE ticket_type_enum ADD VALUE IF NOT EXISTS 'INFORMATION_REQUEST'")
        op.execute("ALTER TYPE ticket_type_enum ADD VALUE IF NOT EXISTS 'CONSULTATION'")

    # 2) due_date nullable
    op.alter_column(
        "tickets",
        "due_date",
        existing_type=sa.Date(),
        nullable=True,
    )

    # 3) needs_sla_validation
    op.add_column(
        "tickets",
        sa.Column(
            "needs_sla_validation",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        "ix_tickets_needs_sla_validation",
        "tickets",
        ["needs_sla_validation"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_tickets_needs_sla_validation", table_name="tickets")
    op.drop_column("tickets", "needs_sla_validation")

    op.alter_column(
        "tickets",
        "due_date",
        existing_type=sa.Date(),
        nullable=False,
    )