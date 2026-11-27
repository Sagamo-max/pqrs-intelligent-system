from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.core.database import get_db
from app.schemas.dashboard import DashboardMetricsResponse
from app.services.dashboard_service import get_dashboard_metrics

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/metricas",
    response_model=DashboardMetricsResponse,
    status_code=status.HTTP_200_OK,
)
def read_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Devuelve métricas agregadas en tiempo real sobre las PQRS (HU-19)."""
    return get_dashboard_metrics(db=db, current_user=current_user)
