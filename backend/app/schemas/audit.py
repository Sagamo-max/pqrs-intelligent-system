from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AIAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    provider: str
    ai_model: str
    original_text: str
    sanitized_text: str
    decision_justification: str
    suggested_type: str
    suggested_priority: str
    suggested_area_code: str
    confidence: float | None
    tokens_used: int | None
    latency_ms: int | None
    raw_response: dict | None
    created_at: datetime