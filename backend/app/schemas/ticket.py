from pydantic import BaseModel, EmailStr, Field

class ClaimantCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    document_type: str = Field(pattern="^(CC|CE|NIT|TI|PASAPORTE)$")
    document_number: str = Field(min_length=5, max_length=20)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=15)

class TicketCreate(BaseModel):
    claimant: ClaimantCreate
    free_text: str = Field(min_length=20, max_length=2000)

class TicketResponse(BaseModel):
    ticket_number: str
    status: str