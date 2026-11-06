from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import require_role
from app.core.database import get_db
from app.models.funcionario import FuncionarioRole
from app.models.outbox_event import OutboxEvent

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.get("/pending")
def get_pending_events(
    db: Session = Depends(get_db),
    _: object = Depends(require_role(FuncionarioRole.MASTER)),
):
    events = db.scalars(
        select(OutboxEvent)
        .where(OutboxEvent.processed.is_(False))
        .order_by(OutboxEvent.created_at)
    ).all()
    return [
        {"event_id": str(event.event_id), "event_type": event.event_type, "payload": event.payload}
        for event in events
    ]


@router.post("/{event_id}/ack")
def acknowledge_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(FuncionarioRole.MASTER)),
):
    event = db.scalar(select(OutboxEvent).where(OutboxEvent.event_id == event_id))
    if event:
        event.processed = True
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "acknowledged"}
