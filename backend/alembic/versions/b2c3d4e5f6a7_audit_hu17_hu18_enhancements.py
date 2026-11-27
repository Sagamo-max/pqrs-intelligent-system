"""audit_hu17_hu18_enhancements

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-26 21:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for HU-17 and HU-18 auditability enhancements."""
    # HU-18: Vincular change_audits con funcionarios.id
    op.add_column(
        "change_audits",
        sa.Column("funcionario_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_change_audits_funcionario_id",
        "change_audits",
        "funcionarios",
        ["funcionario_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_change_audits_funcionario_id",
        "change_audits",
        ["funcionario_id"],
    )
    op.create_index(
        "ix_change_audits_ticket_created",
        "change_audits",
        ["ticket_id", "created_at"],
    )

    # HU-17: Permitir múltiples decisiones IA históricas por ticket
    op.drop_index("ix_ai_audits_ticket_id", table_name="ai_audits")
    op.create_index(
        "ix_ai_audits_ticket_id",
        "ai_audits",
        ["ticket_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_audits_ticket_created",
        "ai_audits",
        ["ticket_id", "created_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ai_audits_ticket_created", table_name="ai_audits")
    op.drop_index("ix_ai_audits_ticket_id", table_name="ai_audits")
    op.create_index(
        "ix_ai_audits_ticket_id",
        "ai_audits",
        ["ticket_id"],
        unique=True,
    )

    op.drop_index("ix_change_audits_ticket_created", table_name="change_audits")
    op.drop_index("ix_change_audits_funcionario_id", table_name="change_audits")
    op.drop_constraint(
        "fk_change_audits_funcionario_id",
        "change_audits",
        type_="foreignkey",
    )
    op.drop_column("change_audits", "funcionario_id")
