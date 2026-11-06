import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.outbox_event import OutboxEvent
from app.models.ticket import Ticket
from app.schemas.events import (
    EventClaimantData,
    EventClassificationData,
    EventTextData,
    EventTicketData,
    PqrsCreatedEvent,
)

logger = logging.getLogger(__name__)


def publish_pqrs_created(db: Session, ticket: Ticket) -> None:
    """Create and persist a PQRS_CREADA event in the outbox."""
    try:
        audit = ticket.ai_audit
        claimant = ticket.claimant
        event = PqrsCreatedEvent(
            ticket=EventTicketData(
                ticket_id=ticket.id,
                tracking_number=ticket.tracking_number,
                ticket_type=ticket.ticket_type.value,
                priority=ticket.priority.value,
                status=ticket.status.value,
                area_code=ticket.area.code if ticket.area else "ATENCION_USUARIO",
                due_date=ticket.due_date,
                created_at=ticket.created_at,
                external_reference=ticket.tracking_number,
                organization_id=(
                    str(ticket.organization_id) if ticket.organization_id else None
                ),
            ),
            claimant=EventClaimantData(
                claimant_id=claimant.id,
                full_name=f"{claimant.first_name} {claimant.last_name}".strip(),
                document_type=claimant.document_type,
                document_number=claimant.document_number,
                email=claimant.email,
                phone=claimant.phone,
            ),
            classification=EventClassificationData(
                source=audit.classification_source if audit else "fallback",
                justification=audit.decision_justification if audit else "",
                tokens_used=audit.tokens_used if audit else None,
                latency_ms=audit.latency_ms if audit else None,
            ),
            text=EventTextData(sanitized=audit.sanitized_text if audit else ""),
        )
        db.add(
            OutboxEvent(
                event_id=event.event_id,
                event_type=event.event,
                payload=event.model_dump(mode="json"),
                processed=False,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.flush()
        logger.info("Event PQRS_CREADA published to outbox: %s", event.event_id)
    except Exception:
        logger.exception("Failed to publish PQRS_CREADA event")
        db.rollback()
