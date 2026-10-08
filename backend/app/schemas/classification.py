from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.models.ticket import TicketPriority, TicketType


class AreaCode(str, Enum):
    ATENCION_USUARIO = "ATENCION_USUARIO"
    FACTURACION = "FACTURACION"
    CARTERA = "CARTERA"
    VENTAS = "VENTAS"
    SOPORTE_TECNICO = "SOPORTE_TECNICO"
    TI = "TI"
    LOGISTICA = "LOGISTICA"
    TALENTO_HUMANO = "TALENTO_HUMANO"
    ADMINISTRACION = "ADMINISTRACION"
    JURIDICA = "JURIDICA"


class TicketClassification(BaseModel):
    ticket_type: TicketType = Field(
        description="Primary classification based on the user's intent."
    )
    priority: TicketPriority = Field(
        description="Urgency level. Claims are usually high priority and suggestions low priority."
    )
    responsible_area: AreaCode = Field(
        description="Area from the official catalog responsible for resolving the request."
    )
    decision_justification: str = Field(
        min_length=10,
        max_length=500,
        description=(
            "Required concise explanation (at least 10 characters) for the selected "
            "type, priority, and area. Used for auditing."
        ),
    )

    @field_validator("decision_justification")
    @classmethod
    def not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("decision_justification cannot be empty or whitespace")
        if len(stripped) < 10:
            raise ValueError("decision_justification must be at least 10 characters")
        return stripped