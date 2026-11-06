import logging
import uuid
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus, TicketType
from app.services.area_service import resolve_area
from app.services.audit_service import create_ai_audit, create_audit_attempts
from app.services.classifier import classify_ticket_text
from app.services.sanitizer_service import sanitize_text
from app.services.sla import calculate_due_date

logger = logging.getLogger(__name__)


def generate_tracking_number() -> str:
    return f"PQRS-{uuid.uuid4().hex[:8].upper()}"


def create_ticket(
    db: Session, free_text: str, claimant_id, organization_id: UUID
) -> Ticket:
    try:
        filing_date = date.today()

        ticket = Ticket(
            tracking_number=generate_tracking_number(),
            original_text=free_text,
            claimant_id=claimant_id,
            organization_id=organization_id,
            ticket_type=TicketType.PETITION,
            priority="MEDIUM",
            status=TicketStatus.RECEIVED,
            filing_date=filing_date,
            due_date=None,
            needs_sla_validation=False,
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

        # --- CÁLCULO DETERMINISTA DEL SLA (HU-10) ---
        due_date = calculate_due_date(filing_date, classification.ticket_type)
        if due_date is None:
            ticket.due_date = None
            ticket.needs_sla_validation = True
            logger.warning(
                "Ticket %s clasificado como CONSULTATION. "
                "Requiere validación humana del SLA.",
                ticket.id,
            )
        else:
            ticket.due_date = due_date
            ticket.needs_sla_validation = False
        # ---------------------------------------------

        create_ai_audit(db=db, ticket_id=ticket.id, outcome=outcome, original_text=free_text, sanitized_text=sanitized_text)
        create_audit_attempts(db=db, ticket_id=ticket.id, attempts=outcome.attempts)

        db.commit()
        db.refresh(ticket)
        from app.services.event_publisher import publish_pqrs_created

        publish_pqrs_created(db, ticket)
        db.commit()
        from app.services.companero_client import send_pqr_to_companero

        send_pqr_to_companero(db, ticket)
        return ticket

    except Exception:
        db.rollback()
        raise