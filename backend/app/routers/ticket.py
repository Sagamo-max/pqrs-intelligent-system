import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth_deps import get_current_user
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket
from app.schemas.classification import TicketClassification
from app.schemas.ticket import (
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketTypeChangeRequest,
)
from app.services.change_audit_service import create_change_audit
from app.services.claimant_service import get_or_create_claimant
from app.services.classifier import classify_ticket_text
from app.services.sla import calculate_due_date
from app.services.ticket_service import create_ticket

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/pqrs",
    tags=["Tickets"],
    dependencies=[Depends(get_current_user)],
)


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


@router.get("/", response_model=TicketListResponse | list[TicketResponse])
def list_tickets(
    ticket_type: str | None = None,
    status: str | None = None,
    area_id: UUID | None = None,
    priority: str | None = None,
    limit: int = 20,
    offset: int = 0,
    needs_sla_validation: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit must be between 1 and 100",
        )
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="offset must be non-negative",
        )

    filters = []
    if current_user.role == FuncionarioRole.ANALISTA:
        filters.append(Ticket.area_id == current_user.area_id)
    if ticket_type is not None:
        filters.append(Ticket.ticket_type == ticket_type)
    if status is not None:
        filters.append(Ticket.status == status)
    if area_id is not None:
        filters.append(Ticket.area_id == area_id)
    if priority is not None:
        filters.append(Ticket.priority == priority)
    if needs_sla_validation is not None:
        filters.append(Ticket.needs_sla_validation.is_(needs_sla_validation))

    if needs_sla_validation is not None:
        return list(
            db.scalars(
                select(Ticket)
                .where(*filters)
                .order_by(Ticket.created_at.desc())
            )
        )

    total = db.scalar(
        select(func.count()).select_from(Ticket).where(*filters)
    ) or 0
    tickets = db.scalars(
        select(Ticket)
        .where(*filters)
        .order_by(Ticket.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return TicketListResponse(
        items=tickets,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{tracking_number}/tipo",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
def change_ticket_type(
    tracking_number: str,
    payload: TicketTypeChangeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Reclasifica un ticket y recalcula su SLA con la regla determinista
    correspondiente al nuevo tipo (Ley 1755 de 2015).

    - Si el nuevo tipo es CONSULTATION, deja `due_date = NULL` y marca
        `needs_sla_validation = True` (salvaguarda legal).
    - Registra el cambio en `ChangeAudit` con quién lo hizo, valores
        anterior/nuevo y motivo.
    """
    stmt = select(Ticket).where(Ticket.tracking_number == tracking_number)
    if current_user.role == FuncionarioRole.ANALISTA:
        stmt = stmt.where(Ticket.area_id == current_user.area_id)
    ticket = db.scalar(stmt)
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