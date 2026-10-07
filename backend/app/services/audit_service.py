from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit import AIAudit
from app.schemas.classification import TicketClassification


def create_ai_audit(
    db: Session,
    ticket_id,
    classification: TicketClassification,
    original_text: str,
    sanitized_text: str,
) -> AIAudit:
    audit = AIAudit(
        ticket_id=ticket_id,
        ai_model=settings.AI_MODEL_NAME,
        provider=settings.AI_PROVIDER,
        original_text=original_text,
        sanitized_text=sanitized_text,
        decision_justification=classification.decision_justification,
        suggested_type=classification.ticket_type,
        suggested_priority=classification.priority,
        suggested_area_code=classification.responsible_area.value,
    )
    db.add(audit)
    db.flush()
    return audit