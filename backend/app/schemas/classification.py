from pydantic import BaseModel, Field
from typing import Literal

class TicketClassification(BaseModel):
    ticket_type: Literal["Peticion", "Queja", "Reclamo", "Sugerencia"] = Field(
        description="Primary classification based on the user's intent."
    )
    priority: Literal["Alta", "Media", "Baja"] = Field(
        description="Urgency level. Claims are usually high priority and suggestions low priority."
    )
    responsible_area: str = Field(
        description="Company department responsible for resolving the request."
    )
    decision_justification: str = Field(
        description="Required concise explanation for the selected type, priority, and department. Used for auditing."
    )