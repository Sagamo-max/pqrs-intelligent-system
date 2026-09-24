from pydantic import BaseModel, Field
from app.models.ticket import TicketType, TicketPriority

class TicketClassification(BaseModel):
    ticket_type: TicketType = Field(
        description="Primary classification based on the user's intent."
    )
    priority: TicketPriority = Field(
        description="Urgency level. Claims are usually high priority and suggestions low priority."
    )
    responsible_area: str = Field(
        max_length=20,
        description="Company department responsible for resolving the request."
    )
    decision_justification: str = Field(
        description="Required concise explanation for the selected type, priority, and department. Used for auditing."
    )