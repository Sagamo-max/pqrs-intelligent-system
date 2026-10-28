import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.area import AreaOut

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



class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tracking_number: str
    status: str
    area: AreaOut | None = None
    

class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID         
    code: str
    name: str


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tracking_number: str
    status: str
    ticket_type: TicketType  # nuevo
    priority: TicketPriority  # nuevo
    filing_date: date  # nuevo
    due_date: date | None  # nuevo (puede ser None)
    needs_sla_validation: bool  # nuevo
    area: AreaOut | None = None


class TicketTypeChangeRequest(BaseModel):
    """Payload para reclasificar el tipo de un ticket (HU-11)."""

    ticket_type: TicketType
    responsible_user: str = Field(..., min_length=3, max_length=100)
    change_reason: str | None = Field(None, max_length=500)