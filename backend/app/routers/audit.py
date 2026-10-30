from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth_deps import get_current_user
from app.models.audit import AIAudit
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket
from app.schemas.audit import AIAuditOut

router = APIRouter(
    prefix="/pqrs",
    tags=["Audit"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/{tracking_number}/audit",
    response_model=AIAuditOut,
    status_code=status.HTTP_200_OK,
)
def get_ticket_audit(
    tracking_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stmt = select(Ticket).where(Ticket.tracking_number == tracking_number)
    if current_user.role == FuncionarioRole.ANALISTA:
        stmt = stmt.where(Ticket.area_id == current_user.area_id)
    ticket = db.scalar(stmt)
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    audit = db.scalar(select(AIAudit).where(AIAudit.ticket_id == ticket.id))
    if not audit:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No AI audit found for this ticket",
        )

    return audit