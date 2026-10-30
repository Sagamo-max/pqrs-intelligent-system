from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlertLevel(str, Enum):
    OVERDUE = "OVERDUE"
    DUE_SOON = "DUE_SOON"
    NORMAL = "NORMAL"
    NO_DUE_DATE = "NO_DUE_DATE"


class TicketAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tracking_number: str
    status: str
    due_date: date | None
    alert_level: AlertLevel
    days_remaining: int | None
