from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_role
from app.core.database import get_db
from app.models.audit import AIAudit
from app.models.funcionario import FuncionarioRole
from app.schemas.audit import AIAuditOut
from app.services.ticket_service import get_ticket_by_identifier

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
    ticket = get_ticket_by_identifier(db, tracking_number, current_user)
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    audit = db.scalar(
        select(AIAudit)
        .where(AIAudit.ticket_id == ticket.id)
        .order_by(AIAudit.created_at.desc())
    )
    if not audit:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No AI audit found for this ticket",
        )

    return audit


@router.get(
    "/{ticket_id}/auditoria-ia",
    response_model=list[AIAuditOut],
    status_code=status.HTTP_200_OK,
)
def get_ticket_ai_audit_history(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(FuncionarioRole.SUPERVISOR)),
):
    """Consulta el histórico completo de decisiones IA de una PQRS (HU-17)."""
    ticket = get_ticket_by_identifier(db, ticket_id, current_user)
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    audits = db.scalars(
        select(AIAudit)
        .where(AIAudit.ticket_id == ticket.id)
        .order_by(AIAudit.created_at.asc())
    ).all()
    return list(audits)
