import uuid
from sqlalchemy.orm import Session
from app.models.ticket import Ticket, TicketStatus
from app.services.sla import calculate_due_date

def generate_tracking_number() -> str:
    return f"PQRS-{uuid.uuid4().hex[:8].upper()}"

def create_ticket(db: Session, free_text: str, claimant_id: str) -> Ticket:
    ticket = Ticket(
        tracking_number=generate_tracking_number(),
        original_text=free_text,
        claimant_id=claimant_id,
        ticket_type="PETITION",
        priority="MEDIUM",
        status=TicketStatus.RECEIVED,
        due_date=calculate_due_date()
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return ticket