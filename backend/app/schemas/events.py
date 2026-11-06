from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventTicketData(BaseModel):
    ticket_id: UUID
    tracking_number: str
    ticket_type: str
    priority: str
    status: str
    area_code: str
    due_date: date | None
    created_at: datetime
    external_reference: str
    organization_id: str | None


class EventClaimantData(BaseModel):
    claimant_id: UUID
    full_name: str
    document_type: str
    document_number: str
    email: str
    phone: str | None


class EventClassificationData(BaseModel):
    source: str
    justification: str
    tokens_used: int | None = None
    latency_ms: int | None = None


class EventTextData(BaseModel):
    sanitized: str


class PqrsCreatedEvent(BaseModel):
    event: str = "PQRS_CREADA"
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ticket: EventTicketData
    claimant: EventClaimantData
    classification: EventClassificationData
    text: EventTextData
