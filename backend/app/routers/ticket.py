import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ticket import Ticket
from app.schemas.classification import TicketClassification
from app.schemas.ticket import TicketCreate, TicketResponse, TicketTypeChangeRequest
from app.services.change_audit_service import create_change_audit
from app.services.claimant_service import get_or_create_claimant
from app.services.classifier import classify_ticket_text
from app.services.sla import calculate_due_date
from app.services.ticket_service import create_ticket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pqrs", tags=["Tickets"])


class TicketClassificationRequest(BaseModel):
    text: str


@router.post("/classify-poc", response_model=TicketClassification)
def classify_ticket(payload: TicketClassificationRequest):
    try:
        return classify_ticket_text(payload.text)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def submit_ticket(request: TicketCreate, db: Session = Depends(get_db)):
    try:
        claimant = get_or_create_claimant(db=db, claimant_data=request.claimant)

        ticket = create_ticket(
            db=db,
            free_text=request.free_text,
            claimant_id=claimant.id,
        )

        return TicketResponse.model_validate(ticket)

    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to create PQRS: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=list[TicketResponse])
def list_tickets(
    needs_sla_validation: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Lista los tickets ordenados por fecha de creación (más recientes primero).

    Si `needs_sla_validation=true`, filtra los tickets que requieren validación
    humana del SLA (por ejemplo, los clasificados como CONSULTATION).
    """
    stmt = select(Ticket).order_by(Ticket.created_at.desc())
    if needs_sla_validation is not None:
        stmt = stmt.where(Ticket.needs_sla_validation.is_(needs_sla_validation))
    return list(db.scalars(stmt))


@router.patch(
    "/{tracking_number}/tipo",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
def change_ticket_type(
    tracking_number: str,
    payload: TicketTypeChangeRequest,
    db: Session = Depends(get_db),
):
    """
    Reclasifica un ticket y recalcula su SLA con la regla determinista
    correspondiente al nuevo tipo (Ley 1755 de 2015).

    - Si el nuevo tipo es CONSULTATION, deja `due_date = NULL` y marca
        `needs_sla_validation = True` (salvaguarda legal).
    - Registra el cambio en `ChangeAudit` con quién lo hizo, valores
        anterior/nuevo y motivo.
    """
    ticket = db.scalar(
        select(Ticket).where(Ticket.tracking_number == tracking_number)
    )
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    old_type = ticket.ticket_type
    new_type = payload.ticket_type

    if old_type == new_type:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Ticket is already classified as {new_type.value}",
        )

    # Recalcular SLA con el nuevo tipo
    new_due_date = calculate_due_date(ticket.filing_date, new_type)

    # Actualizar el ticket
    ticket.ticket_type = new_type
    if new_due_date is None:
        ticket.due_date = None
        ticket.needs_sla_validation = True
        logger.warning(
            "Ticket %s reclasificado a CONSULTATION. "
            "Requiere validación humana del SLA.",
            ticket.id,
        )
    else:
        ticket.due_date = new_due_date
        ticket.needs_sla_validation = False

    # Registrar auditoría del cambio
    create_change_audit(
        db=db,
        ticket_id=ticket.id,
        responsible_user=payload.responsible_user,
        event_type="TICKET_TYPE_CHANGE",
        modified_field="ticket_type",
        old_value=old_type.value,
        new_value=new_type.value,
        change_reason=payload.change_reason,
    )

    db.commit()
    db.refresh(ticket)
    return TicketResponse.model_validate(ticket)