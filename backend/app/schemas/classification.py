from enum import Enum

from pydantic import BaseModel, Field

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
        description="Required concise explanation for the selected type, priority, and area. Used for auditing."
    )