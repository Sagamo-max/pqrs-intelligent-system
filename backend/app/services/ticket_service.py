import uuid

from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus
from app.services.area_service import resolve_area
from app.services.audit_service import create_ai_audit, create_audit_attempts
from app.services.classifier import classify_ticket_text
from app.services.sanitizer_service import sanitize_text
from app.services.sla import calculate_due_date


def generate_tracking_number() -> str:
    return f"PQRS-{uuid.uuid4().hex[:8].upper()}"


def create_ticket(db: Session, free_text: str, claimant_id) -> Ticket:
    try:
        ticket = Ticket(
            tracking_number=generate_tracking_number(),
            original_text=free_text,
            claimant_id=claimant_id,
            ticket_type="PETITION",
            priority="MEDIUM",
            status=TicketStatus.RECEIVED,
            due_date=calculate_due_date(),
        )
        db.add(ticket)
        db.flush()

        sanitized_text = sanitize_text(free_text)

        outcome = classify_ticket_text(sanitized_text)
        classification = outcome.classification

        area = resolve_area(db, classification.responsible_area.value)

        ticket.ticket_type = classification.ticket_type
        ticket.priority = classification.priority
        ticket.area_id = area.id

        create_ai_audit(
            db=db,
            ticket_id=ticket.id,
            outcome=outcome,
            original_text=free_text,
            sanitized_text=sanitized_text,
        )

        create_audit_attempts(
            db=db,
            ticket_id=ticket.id,
            attempts=outcome.attempts,
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception:
        db.rollback()
        raise