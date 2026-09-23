import uuid
from sqlalchemy.orm import Session
from app.models.claimant import Claimant
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate
from app.services.sla import calculate_due_date

def generate_tracking_number() -> str:
    return f"PQRS-{uuid.uuid4().hex[:8].upper()}"

def create_ticket(db: Session, ticket_data: TicketCreate) -> Ticket:
    claimant = db.query(Claimant).filter(
        Claimant.document_number == ticket_data.claimant.document_number
    ).first()

    if not claimant:
        claimant = Claimant(
            first_name=ticket_data.claimant.full_name,
            last_name="",
            document_type=ticket_data.claimant.document_type,
            document_number=ticket_data.claimant.document_number,
            email=ticket_data.claimant.email,
            phone=ticket_data.claimant.phone
        )
        db.add(claimant)
        db.commit()
        db.refresh(claimant)

    ticket = Ticket(
        tracking_number=generate_tracking_number(),
        original_text=ticket_data.free_text,
        claimant_id=claimant.id,
        ticket_type="PETITION",
        priority="MEDIUM",
        status=TicketStatus.RECEIVED,
        due_date=calculate_due_date()
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket