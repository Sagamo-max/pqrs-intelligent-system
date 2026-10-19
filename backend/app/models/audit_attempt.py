import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AIAuditAttempt(Base):
    __tablename__ = "ai_audit_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attempt_number = Column(Integer, nullable=False)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ticket = relationship("Ticket", backref="ai_audit_attempts")