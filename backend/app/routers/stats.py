from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.core.database import get_db
from app.models.audit import AIAudit
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket
from app.schemas.stats import PeriodStats, SourceCount, StatsResponse

router = APIRouter(
    prefix="/pqrs",
    tags=["Stats"],
    dependencies=[Depends(get_current_user)],
)


def _build_period_stats(
    db: Session,
    current_user,
    since: datetime | None = None,
) -> PeriodStats:
    stmt = select(
        func.count(AIAudit.id).label("total"),
        func.sum(case((AIAudit.classification_source == "openai", 1), else_=0)).label("openai"),
        func.sum(case((AIAudit.classification_source == "heuristic", 1), else_=0)).label("heuristic"),
        func.sum(case((AIAudit.classification_source == "fallback", 1), else_=0)).label("fallback"),
    ).join(Ticket, Ticket.id == AIAudit.ticket_id)
    if current_user.role == FuncionarioRole.ANALISTA:
        stmt = stmt.where(Ticket.area_id == current_user.area_id)
    if since is not None:
        stmt = stmt.where(AIAudit.created_at >= since)

    row = db.execute(stmt).one()
    return PeriodStats(
        total=row.total or 0,
        by_source=SourceCount(
            openai=row.openai or 0,
            heuristic=row.heuristic or 0,
            fallback=row.fallback or 0,
        ),
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return StatsResponse(
        last_24h=_build_period_stats(db, current_user, since=cutoff),
        all_time=_build_period_stats(db, current_user),
    )