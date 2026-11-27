import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.core.database import get_db
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket
from app.schemas.classification import TicketClassification
from app.schemas.ticket import (
    TicketAreaReassignRequest,
    TicketCreate,
    TicketDetailResponse,
    TicketListResponse,
    TicketPriorityChangeRequest,
    TicketResponse,
    TicketTypeChangeRequest,
)
from app.services.change_audit_service import create_change_audit
from app.services.claimant_service import get_or_create_claimant
from app.services.classifier import classify_ticket_text
from app.services.sla import calculate_due_date
from app.services.ticket_service import (
    change_ticket_priority,
    create_ticket,
    get_ticket_by_identifier,
    get_ticket_detail,
    reassign_ticket_area,
)

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
    ticket = get_ticket_by_identifier(db, tracking_number, current_user)
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
        funcionario_id=getattr(current_user, "id", None),
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


@router.patch(
    "/{ticket_id}/area",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
def reassign_area_endpoint(
    ticket_id: str,
    payload: TicketAreaReassignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reasigna manualmente el área responsable de una PQRS sin alterar estado ni SLA (HU-15)."""
    ticket = reassign_ticket_area(
        db=db,
        identifier=ticket_id,
        area_id=payload.area_id,
        current_user=current_user,
        change_reason=payload.change_reason,
        responsible_user=payload.responsible_user,
    )
    return TicketResponse.model_validate(ticket)


@router.patch(
    "/{ticket_id}/prioridad",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
def change_priority_endpoint(
    ticket_id: str,
    payload: TicketPriorityChangeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Modifica manualmente la prioridad de una PQRS y registra intervención humana (HU-18)."""
    ticket = change_ticket_priority(
        db=db,
        identifier=ticket_id,
        new_priority=payload.priority,
        current_user=current_user,
        change_reason=payload.change_reason,
        responsible_user=payload.responsible_user,
    )
    return TicketResponse.model_validate(ticket)


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_ticket_detail_endpoint(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Devuelve detalle completo de PQRS con solicitante, IA, SLA y línea de tiempo (HU-16)."""
    return get_ticket_detail(db=db, identifier=ticket_id, current_user=current_user)
