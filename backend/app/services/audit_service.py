from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit import AIAudit
from app.services.classifier import ClassificationOutcome


def create_ai_audit(
    db: Session,
    ticket_id,
    outcome: ClassificationOutcome,
    original_text: str,
    sanitized_text: str,
) -> AIAudit:
    classification = outcome.classification

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
        raw_response=outcome.raw_response,
        tokens_used=outcome.tokens_used,
        latency_ms=outcome.latency_ms,
        confidence=outcome.confidence,
    )
    db.add(audit)
    db.flush()
    return audit