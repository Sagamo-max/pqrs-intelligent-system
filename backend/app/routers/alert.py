from datetime import date

import holidays_co_full
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.core.database import get_db
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket, TicketStatus
from app.schemas.alert import AlertLevel, TicketAlertOut

router = APIRouter(
    prefix="/pqrs",
    tags=["Alerts"],
    dependencies=[Depends(get_current_user)],
)


def _alert_level(
    due_date: date | None,
    today: date,
    due_soon_limit: date,
) -> AlertLevel:
    if due_date is None:
        return AlertLevel.NO_DUE_DATE
    if due_date < today:
        return AlertLevel.OVERDUE
    if due_date <= due_soon_limit:
        return AlertLevel.DUE_SOON
    return AlertLevel.NORMAL


@router.get("/alerts", response_model=list[TicketAlertOut])
def list_ticket_alerts(
    level: AlertLevel | None = None,
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    today = date.today()
    due_soon_limit = holidays_co_full.add_business_days(today, 3)
    stmt = (
        select(Ticket)
        .where(Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]))
        .order_by(Ticket.due_date.asc().nulls_last(), Ticket.created_at.asc())
    )
    if current_user.role == FuncionarioRole.ANALISTA:
        stmt = stmt.where(Ticket.area_id == current_user.area_id)
    tickets = db.scalars(stmt).all()

    alerts = []
    for ticket in tickets:
        alert_level = _alert_level(ticket.due_date, today, due_soon_limit)
        if level is None and alert_level not in {
            AlertLevel.OVERDUE,
            AlertLevel.DUE_SOON,
        }:
            continue
        if level is not None and alert_level != level:
            continue

        days_remaining = (
            (ticket.due_date - today).days if ticket.due_date is not None else None
        )
        alerts.append(
            TicketAlertOut(
                id=ticket.id,
                tracking_number=ticket.tracking_number,
                status=ticket.status,
                due_date=ticket.due_date,
                alert_level=alert_level,
                days_remaining=days_remaining,
            )
        )

    return alerts[offset : offset + limit]
