"""add_ai_audit_attempts_and_classification_source

Revision ID: fc9b7aa1bd27
Revises: 0260da80b911
Create Date: 2026-10-16 09:53:01.399052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fc9b7aa1bd27'
down_revision: Union[str, Sequence[str], None] = '0260da80b911'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Nueva columna en ai_audits
    op.add_column(
        "ai_audits",
        sa.Column(
            "classification_source",
            sa.String(length=20),
            nullable=False,
            server_default="openai",
        ),
    )

    # 2) Nueva tabla ai_audit_attempts
    op.create_table(
        "ai_audit_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(length=100), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_audit_attempts_id", "ai_audit_attempts", ["id"])
    op.create_index(
        "ix_ai_audit_attempts_ticket_id", "ai_audit_attempts", ["ticket_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ai_audit_attempts_ticket_id", table_name="ai_audit_attempts")
    op.drop_index("ix_ai_audit_attempts_id", table_name="ai_audit_attempts")
    op.drop_table("ai_audit_attempts")

    op.drop_column("ai_audits", "classification_source")