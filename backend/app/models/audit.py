import uuid
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.ticket import PQRSType, PQRSPriority


class AIAudit(Base):
    __tablename__ = "ai_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("pqrs_tickets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    ai_model = Column(String(50), nullable=False)
    provider = Column(String(20), nullable=False)

    decision_justification = Column(Text, nullable=False)

    suggested_type = Column(SQLEnum(PQRSType, name="pqrs_type_enum", create_type=False), nullable=False)
    suggested_priority = Column(SQLEnum(PQRSPriority, name="pqrs_priority_enum", create_type=False), nullable=False)
    suggested_department_code = Column(String(20), nullable=False)

    confidence = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    raw_response = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("PQRSTicket", back_populates="ai_audit")


class ChangeAudit(Base):
    __tablename__ = "change_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("pqrs_tickets.id", ondelete="CASCADE"), nullable=False, index=True)

    responsible_user = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)
    modified_field = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("PQRSTicket", back_populates="change_audits")