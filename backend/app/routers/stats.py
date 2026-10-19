from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import AIAudit
from app.schemas.stats import PeriodStats, SourceCount, StatsResponse

router = APIRouter(prefix="/pqrs", tags=["Stats"])


def _build_period_stats(db: Session, since: datetime | None = None) -> PeriodStats:
    stmt = select(
        func.count(AIAudit.id).label("total"),
        func.sum(case((AIAudit.classification_source == "openai", 1), else_=0)).label("openai"),
        func.sum(case((AIAudit.classification_source == "heuristic", 1), else_=0)).label("heuristic"),
        func.sum(case((AIAudit.classification_source == "fallback", 1), else_=0)).label("fallback"),
    )
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
def get_stats(db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return StatsResponse(
        last_24h=_build_period_stats(db, since=cutoff),
        all_time=_build_period_stats(db),
    )