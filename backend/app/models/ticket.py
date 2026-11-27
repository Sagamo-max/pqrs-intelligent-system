import enum
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TicketType(str, enum.Enum):
    PETITION = "PETITION"
    COMPLAINT = "COMPLAINT"
    CLAIM = "CLAIM"
    SUGGESTION = "SUGGESTION"
    INFORMATION_REQUEST = "INFORMATION_REQUEST"  
    CONSULTATION = "CONSULTATION" 


class TicketPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TicketStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    claimant_id = Column(UUID(as_uuid=True), ForeignKey("claimants.id", ondelete="RESTRICT"), nullable=False, index=True)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", ondelete="RESTRICT"), nullable=True, index=True)

    tracking_number = Column(String(30), unique=True, nullable=False, index=True)
    original_text = Column(Text, nullable=False)

    ticket_type = Column(SQLEnum(TicketType, name="ticket_type_enum"), nullable=False, index=True)
    priority = Column(SQLEnum(TicketPriority, name="ticket_priority_enum"), nullable=False, default=TicketPriority.MEDIUM)
    status = Column(SQLEnum(TicketStatus, name="ticket_status_enum"), nullable=False, default=TicketStatus.RECEIVED)

    filing_date = Column(Date, server_default=func.current_date(), nullable=False)
    due_date = Column(Date, nullable=True, index=True)
    needs_sla_validation = Column(Boolean, default=False, nullable=False, index=True)  # nuevo

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    claimant = relationship("Claimant", back_populates="tickets")
    area = relationship("Area", back_populates="tickets")
    ai_audit = relationship("AIAudit", uselist=False, viewonly=True, order_by="AIAudit.created_at.desc()")
    ai_audits = relationship("AIAudit", back_populates="ticket", order_by="AIAudit.created_at.asc()", cascade="all, delete-orphan")
    change_audits = relationship("ChangeAudit", back_populates="ticket", cascade="all, delete-orphan")
    ai_audit_attempts = relationship("AIAuditAttempt", back_populates="ticket", cascade="all, delete-orphan")