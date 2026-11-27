from datetime import date, datetime, timezone

import holidays_co_full
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.area import Area
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketType
from app.schemas.dashboard import AreaMetricOut, DashboardMetricsResponse, SLAMetricsOut


def _enum_key(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def get_dashboard_metrics(db: Session, current_user) -> DashboardMetricsResponse:
    """Ejecuta consultas agregadas (COUNT, GROUP BY) para métricas del dashboard (HU-19)."""
    base_filters = []
    if current_user.role == FuncionarioRole.ANALISTA:
        base_filters.append(Ticket.area_id == current_user.area_id)

    # 1. Totales por tipo (P/Q/R/S y adicionales si existen)
    por_tipo: dict[str, int] = {
        TicketType.PETITION.value: 0,
        TicketType.COMPLAINT.value: 0,
        TicketType.CLAIM.value: 0,
        TicketType.SUGGESTION.value: 0,
    }
    type_stmt = (
        select(Ticket.ticket_type, func.count(Ticket.id))
        .where(*base_filters)
        .group_by(Ticket.ticket_type)
    )
    for t_type, count in db.execute(type_stmt).all():
        por_tipo[_enum_key(t_type)] = int(count or 0)

    # 2. Distribución por área responsable
    area_stmt = (
        select(Area.id, Area.code, Area.name, func.count(Ticket.id))
        .select_from(Ticket)
        .outerjoin(Area, Area.id == Ticket.area_id)
        .where(*base_filters)
        .group_by(Area.id, Area.code, Area.name)
    )
    por_area = [
        AreaMetricOut(
            area_id=row[0],
            area_code=row[1] or "SIN_AREA",
            area_name=row[2] or "Sin área asignada",
            total=int(row[3] or 0),
        )
        for row in db.execute(area_stmt).all()
    ]

    # 3. Distribución por prioridad
    por_prioridad: dict[str, int] = {
        TicketPriority.HIGH.value: 0,
        TicketPriority.MEDIUM.value: 0,
        TicketPriority.LOW.value: 0,
    }
    priority_stmt = (
        select(Ticket.priority, func.count(Ticket.id))
        .where(*base_filters)
        .group_by(Ticket.priority)
    )
    for priority, count in db.execute(priority_stmt).all():
        por_prioridad[_enum_key(priority)] = int(count or 0)

    # 4. Vencidas vs a tiempo
    today = date.today()
    # Garantizar consistencia de calendario colombiano importado
    _ = holidays_co_full.add_business_days(today, 0)
    active_statuses = [TicketStatus.RECEIVED, TicketStatus.IN_PROGRESS]

    is_overdue_expr = (
        (Ticket.due_date.is_not(None))
        & (Ticket.due_date < today)
        & (Ticket.status.in_(active_statuses))
    )
    is_no_sla_expr = Ticket.due_date.is_(None)

    sla_stmt = select(
        func.count(Ticket.id).label("total"),
        func.sum(case((is_overdue_expr, 1), else_=0)).label("vencidas"),
        func.sum(case((is_no_sla_expr, 1), else_=0)).label("sin_fecha_sla"),
        func.sum(
            case(
                ((Ticket.due_date.is_not(None)) & (~is_overdue_expr), 1),
                else_=0,
            )
        ).label("a_tiempo"),
    ).where(*base_filters)

    sla_row = db.execute(sla_stmt).one()
    total_pqrs = int(sla_row.total or 0)
    vencidas = int(sla_row.vencidas or 0)
    sin_fecha_sla = int(sla_row.sin_fecha_sla or 0)
    a_tiempo = int(sla_row.a_tiempo or 0)

    con_sla = vencidas + a_tiempo
    porcentaje_a_tiempo = round((a_tiempo / con_sla) * 100.0, 2) if con_sla > 0 else 0.0

    return DashboardMetricsResponse(
        total_pqrs=total_pqrs,
        por_tipo=por_tipo,
        por_area=por_area,
        por_prioridad=por_prioridad,
        cumplimiento_sla=SLAMetricsOut(
            vencidas=vencidas,
            a_tiempo=a_tiempo,
            sin_fecha_sla=sin_fecha_sla,
            porcentaje_a_tiempo=porcentaje_a_tiempo,
        ),
        generated_at=datetime.now(timezone.utc),
    )
