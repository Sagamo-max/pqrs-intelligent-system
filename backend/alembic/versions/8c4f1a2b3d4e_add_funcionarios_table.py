"""add funcionarios table

Revision ID: 8c4f1a2b3d4e
Revises: f7c866f6b757
Create Date: 2026-10-30 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8c4f1a2b3d4e"
down_revision: Union[str, Sequence[str], None] = "f7c866f6b757"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


funcionario_role_enum = postgresql.ENUM(
    "ANALISTA",
    "SUPERVISOR",
    "MASTER",
    name="funcionario_role_enum",
)
funcionario_role_column_enum = postgresql.ENUM(
    "ANALISTA",
    "SUPERVISOR",
    "MASTER",
    name="funcionario_role_enum",
    create_type=False,
)


def upgrade() -> None:
    funcionario_role_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "funcionarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column(
            "role",
            funcionario_role_column_enum,
            nullable=False,
            server_default="ANALISTA",
        ),
        sa.Column("area_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["areas.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_funcionarios_id", "funcionarios", ["id"])
    op.create_index(
        "ix_funcionarios_username",
        "funcionarios",
        ["username"],
        unique=True,
    )
    op.create_index("ix_funcionarios_area_id", "funcionarios", ["area_id"])


def downgrade() -> None:
    op.drop_index("ix_funcionarios_area_id", table_name="funcionarios")
    op.drop_index("ix_funcionarios_username", table_name="funcionarios")
    op.drop_index("ix_funcionarios_id", table_name="funcionarios")
    op.drop_table("funcionarios")
    funcionario_role_enum.drop(op.get_bind(), checkfirst=True)
