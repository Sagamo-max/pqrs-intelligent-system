"""add organizaciones table

Revision ID: d9f6a3b8c2e1
Revises: c8e5f2a1b4d6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d9f6a3b8c2e1"
down_revision: Union[str, Sequence[str], None] = "c8e5f2a1b4d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_organizaciones_id", "organizaciones", ["id"])
    op.create_index("ix_organizaciones_slug", "organizaciones", ["slug"])
    op.execute(
        """
        INSERT INTO organizaciones (id, name, slug, is_active)
        VALUES (
            '550e8400-e29b-41d4-a716-446655440000',
            'Organización Demo',
            'demo',
            true
        )
        ON CONFLICT (slug) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_organizaciones_slug", table_name="organizaciones")
    op.drop_index("ix_organizaciones_id", table_name="organizaciones")
    op.drop_table("organizaciones")
