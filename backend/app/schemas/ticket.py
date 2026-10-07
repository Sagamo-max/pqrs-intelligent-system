import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.area import AreaOut


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