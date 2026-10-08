from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import AIAudit
from app.models.ticket import Ticket
from app.schemas.audit import AIAuditOut

router = APIRouter(prefix="/pqrs", tags=["Audit"])


@router.get(
    "/{tracking_number}/audit",
    response_model=AIAuditOut,
    status_code=status.HTTP_200_OK,
)
def get_ticket_audit(tracking_number: str, db: Session = Depends(get_db)):
    ticket = db.scalar(
        select(Ticket).where(Ticket.tracking_number == tracking_number)
    )
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    audit = db.scalar(select(AIAudit).where(AIAudit.ticket_id == ticket.id))
    if not audit:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No AI audit found for this ticket",
        )

    return audit