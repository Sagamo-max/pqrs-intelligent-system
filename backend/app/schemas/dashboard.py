from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AreaMetricOut(BaseModel):
    area_id: UUID | None = None
    area_code: str
    area_name: str
    total: int


class SLAMetricsOut(BaseModel):
    vencidas: int
    a_tiempo: int
    sin_fecha_sla: int
    porcentaje_a_tiempo: float


class DashboardMetricsResponse(BaseModel):
    """Métricas agregadas del tablero operativo de PQRS (HU-19)."""

    total_pqrs: int
    por_tipo: dict[str, int]
    por_area: list[AreaMetricOut]
    por_prioridad: dict[str, int]
    cumplimiento_sla: SLAMetricsOut
    generated_at: datetime
