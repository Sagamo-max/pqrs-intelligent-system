import re
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.models.ticket import TicketPriority, TicketType


class ClaimantCreate(BaseModel):
    full_name: str = Field(..., min_length=3)
    document_type: str = Field(...)
    document_number: str = Field(..., min_length=5)
    email: str
    phone: str = Field(...)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format provided")
        return v


class TicketCreate(BaseModel):
    claimant: ClaimantCreate
    free_text: str

    @field_validator("free_text")
    @classmethod
    def validate_meaningful_text(cls, v: str) -> str:
        clean_text = v.strip()
        if not clean_text:
            raise ValueError("Free text cannot be empty or just whitespace")
        if len(clean_text) < 15:
            raise ValueError(
                "Free text must contain at least 15 meaningful characters to be processed"
            )
        return clean_text



class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    tracking_number: str
    status: str
    ticket_type: TicketType
    priority: TicketPriority
    filing_date: date
    due_date: date | None
    needs_sla_validation: bool
    area: AreaOut | None = None


class TicketTypeChangeRequest(BaseModel):
    """Payload para reclasificar el tipo de un ticket (HU-11)."""

    ticket_type: TicketType
    responsible_user: str = Field(..., min_length=3, max_length=100)
    change_reason: str | None = Field(None, max_length=500)


class TicketAreaReassignRequest(BaseModel):
    """Payload para reasignación manual de área responsable (HU-15)."""

    model_config = ConfigDict(populate_by_name=True)

    area_id: UUID = Field(..., validation_alias=AliasChoices("area_id", "id_area"))
    change_reason: str | None = Field(
        None,
        validation_alias=AliasChoices("change_reason", "motivo"),
        max_length=500,
    )
    responsible_user: str | None = Field(None, min_length=3, max_length=100)


class TicketPriorityChangeRequest(BaseModel):
    """Payload para modificación manual de prioridad (HU-18)."""

    model_config = ConfigDict(populate_by_name=True)

    priority: TicketPriority = Field(
        ...,
        validation_alias=AliasChoices("priority", "prioridad"),
    )
    change_reason: str | None = Field(
        None,
        validation_alias=AliasChoices("change_reason", "motivo"),
        max_length=500,
    )
    responsible_user: str | None = Field(None, min_length=3, max_length=100)


class ClaimantDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_type: str
    document_number: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None


class TicketSLADetailOut(BaseModel):
    filing_date: date
    due_date: date | None
    needs_sla_validation: bool
    alert_level: str
    days_remaining: int | None
    is_overdue: bool


class AIAuditSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ai_model: str
    provider: str
    classification_source: str
    suggested_type: str
    suggested_priority: str
    suggested_area_code: str
    decision_justification: str
    confidence: float | None = None
    created_at: datetime


class TimelineEventOut(BaseModel):
    event_id: UUID
    source_type: Literal["AI_DECISION", "HUMAN_INTERVENTION"]
    visual_badge: Literal["IA", "HUMANO"]
    timestamp: datetime
    actor: str
    actor_id: UUID | None = None
    title: str
    description: str
    modified_field: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    details: dict | None = None


class TicketDetailResponse(BaseModel):
    """Respuesta completa de detalle y línea de tiempo de una PQRS (HU-16)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tracking_number: str
    original_text: str
    ticket_type: TicketType
    priority: TicketPriority
    status: str
    created_at: datetime
    updated_at: datetime
    claimant: ClaimantDetailOut
    area: AreaOut | None = None
    sla: TicketSLADetailOut
    clasificacion_ia: AIAuditSummaryOut | None = None
    justificacion_ia: str | None = None
    timeline: list[TimelineEventOut]


class TicketListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tracking_number: str
    ticket_type: str
    priority: str
    status: str
    due_date: date | None
    area: AreaOut | None
    created_at: datetime


class TicketListResponse(BaseModel):
    items: list[TicketListOut]
    total: int
    limit: int
    offset: int