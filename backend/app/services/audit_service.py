from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit import AIAudit
from app.models.audit_attempt import AIAuditAttempt
from app.services.classifier import AttemptInfo, ClassificationOutcome


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
        classification_source=outcome.source,
        raw_response=outcome.raw_response,
        tokens_used=outcome.tokens_used,
        latency_ms=outcome.latency_ms,
        confidence=outcome.confidence,
    )
    db.add(audit)
    db.flush()
    return audit


def create_audit_attempts(
    db: Session,
    ticket_id,
    attempts: list[AttemptInfo],
) -> list[AIAuditAttempt]:
    """Persist each failed attempt to ai_audit_attempts for full traceability."""
    if not attempts:
        return []

    records = [
        AIAuditAttempt(
            ticket_id=ticket_id,
            attempt_number=a.attempt_number,
            error_type=a.error_type,
            error_message=a.error_message,
            latency_ms=a.latency_ms,
        )
        for a in attempts
    ]
    db.add_all(records)
    db.flush()
    return records