import uuid
import enum
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PQRSType(str, enum.Enum):
    PETITION = "PETITION"
    COMPLAINT = "COMPLAINT"
    CLAIM = "CLAIM"
    SUGGESTION = "SUGGESTION"


class PQRSPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PQRSStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class PQRSTicket(Base):
    __tablename__ = "pqrs_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    claimant_id = Column(UUID(as_uuid=True), ForeignKey("claimants.id", ondelete="RESTRICT"), nullable=False, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=True, index=True)

    tracking_number = Column(String(30), unique=True, nullable=False, index=True)
    original_text = Column(Text, nullable=False)

    ticket_type = Column(SQLEnum(PQRSType, name="pqrs_type_enum"), nullable=False, index=True)
    priority = Column(SQLEnum(PQRSPriority, name="pqrs_priority_enum"), nullable=False, default=PQRSPriority.MEDIUM)
    status = Column(SQLEnum(PQRSStatus, name="pqrs_status_enum"), nullable=False, default=PQRSStatus.RECEIVED)

    filing_date = Column(Date, server_default=func.current_date(), nullable=False)
    due_date = Column(Date, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    claimant = relationship("Claimant", back_populates="tickets")
    department = relationship("Department", back_populates="tickets")
    ai_audit = relationship("AIAudit", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    change_audits = relationship("ChangeAudit", back_populates="ticket", cascade="all, delete-orphan")