from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import require_role
from app.core.database import get_db
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket
from app.services.companero_client import send_pqr_to_companero

router = APIRouter(prefix="/api/v1/integration", tags=["Integration"])


@router.post("/companero/resend/{tracking_number}")
def resend_to_companero(
    tracking_number: str,
    db: Session = Depends(get_db),
    _=Depends(require_role(FuncionarioRole.MASTER)),
):
    """Retry sending a PQRS to the companion API."""
    ticket = db.scalar(
        select(Ticket).where(Ticket.tracking_number == tracking_number)
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not send_pqr_to_companero(db, ticket):
        raise HTTPException(
            status_code=502,
            detail="Failed to send to companero API",
        )

    return {"status": "sent", "tracking_number": tracking_number}
