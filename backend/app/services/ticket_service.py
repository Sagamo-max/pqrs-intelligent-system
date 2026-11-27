import logging
import uuid
from datetime import date, datetime, timezone
from uuid import UUID

import holidays_co_full
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.area import Area
from app.models.audit import AIAudit, ChangeAudit
from app.models.funcionario import FuncionarioRole
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketType
from app.schemas.ticket import (
    AIAuditSummaryOut,
    AreaOut,
    ClaimantDetailOut,
    TicketDetailResponse,
    TicketSLADetailOut,
    TimelineEventOut,
)
from app.services.area_service import resolve_area
from app.services.audit_service import create_ai_audit, create_audit_attempts
from app.services.change_audit_service import create_change_audit
from app.services.classifier import classify_ticket_text
from app.services.sla import calculate_due_date

logger = logging.getLogger(__name__)


def generate_tracking_number() -> str:
    return f"PQRS-{uuid.uuid4().hex[:8].upper()}"


def _enum_str(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _normalize_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _compute_sla_state(due_date: date | None, ticket_status) -> tuple[str, int | None, bool]:
    status_val = _enum_str(ticket_status)
    if due_date is None:
        return "NO_DUE_DATE", None, False

    today = date.today()
    days_remaining = (due_date - today).days
    if status_val in {TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value}:
        return "NORMAL", days_remaining, False

    if due_date < today:
        return "OVERDUE", days_remaining, True

    due_soon_limit = holidays_co_full.add_business_days(today, 3)
    if due_date <= due_soon_limit:
        return "DUE_SOON", days_remaining, False

    return "NORMAL", days_remaining, False


def get_ticket_by_identifier(
    db: Session,
    identifier: str,
    current_user,
    *,
    load_relations: bool = False,
) -> Ticket | None:
    """Busca un ticket por UUID o por tracking_number, aplicando alcance de área para ANALISTA."""
    stmt = select(Ticket)
    if load_relations:
        stmt = stmt.options(
            joinedload(Ticket.claimant),
            joinedload(Ticket.area),
            selectinload(Ticket.ai_audits),
            selectinload(Ticket.change_audits).joinedload(ChangeAudit.funcionario),
        )

    try:
        parsed_uuid = UUID(str(identifier))
        stmt = stmt.where(Ticket.id == parsed_uuid)
    except ValueError:
        stmt = stmt.where(Ticket.tracking_number == identifier)

    if current_user.role == FuncionarioRole.ANALISTA:
        stmt = stmt.where(Ticket.area_id == current_user.area_id)

    return db.scalar(stmt)


def create_ticket(db: Session, free_text: str, claimant_id) -> Ticket:
    from app.services.sanitizer_service import sanitize_text

    try:
        filing_date = date.today()

        ticket = Ticket(
            tracking_number=generate_tracking_number(),
            original_text=free_text,
            claimant_id=claimant_id,
            ticket_type=TicketType.PETITION,
            priority="MEDIUM",
            status=TicketStatus.RECEIVED,
            filing_date=filing_date,
            due_date=None,
            needs_sla_validation=False,
        )
        db.add(ticket)
        db.flush()

        sanitized_text = sanitize_text(free_text)
        outcome = classify_ticket_text(sanitized_text)
        classification = outcome.classification

        area = resolve_area(db, classification.responsible_area.value)

        ticket.ticket_type = classification.ticket_type
        ticket.priority = classification.priority
        ticket.area_id = area.id

        # --- CÁLCULO DETERMINISTA DEL SLA (HU-10) ---
        due_date = calculate_due_date(filing_date, classification.ticket_type)
        if due_date is None:
            ticket.due_date = None
            ticket.needs_sla_validation = True
            logger.warning(
                "Ticket %s clasificado como CONSULTATION. "
                "Requiere validación humana del SLA.",
                ticket.id,
            )
        else:
            ticket.due_date = due_date
            ticket.needs_sla_validation = False
        # ---------------------------------------------

        create_ai_audit(
            db=db,
            ticket_id=ticket.id,
            outcome=outcome,
            original_text=free_text,
            sanitized_text=sanitized_text,
        )
        create_audit_attempts(db=db, ticket_id=ticket.id, attempts=outcome.attempts)

        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception:
        db.rollback()
        raise


def reassign_ticket_area(
    db: Session,
    identifier: str,
    area_id: UUID,
    current_user,
    change_reason: str | None = None,
    responsible_user: str | None = None,
) -> Ticket:
    """Reasigna manualmente el área responsable sin alterar estado ni SLA (HU-15)."""
    ticket = get_ticket_by_identifier(db, identifier, current_user)
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    new_area = db.scalar(select(Area).where(Area.id == area_id))
    if not new_area:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Area not found")
    if not new_area.is_active:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Area {new_area.code} is inactive",
        )
    if ticket.area_id == new_area.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Ticket is already assigned to area {new_area.code}",
        )

    old_area_value: str | None = None
    if getattr(ticket, "area", None) is not None:
        old_area_value = ticket.area.code
    elif ticket.area_id is not None:
        old_area = db.scalar(select(Area).where(Area.id == ticket.area_id))
        old_area_value = old_area.code if old_area else str(ticket.area_id)

    # Al reasignar SOLO área NO se altera estado ni se recalcula SLA
    ticket.area_id = new_area.id

    actor = (
        responsible_user
        or getattr(current_user, "username", None)
        or getattr(current_user, "full_name", None)
        or "system"
    )
    create_change_audit(
        db=db,
        ticket_id=ticket.id,
        funcionario_id=getattr(current_user, "id", None),
        responsible_user=actor,
        event_type="AREA_REASSIGNMENT",
        modified_field="area_id",
        old_value=old_area_value,
        new_value=new_area.code,
        change_reason=change_reason or "Reasignación manual de área responsable",
    )

    db.commit()
    db.refresh(ticket)
    return ticket


def change_ticket_priority(
    db: Session,
    identifier: str,
    new_priority: TicketPriority,
    current_user,
    change_reason: str | None = None,
    responsible_user: str | None = None,
) -> Ticket:
    """Modifica manualmente la prioridad de una PQRS y registra auditoría (HU-18)."""
    ticket = get_ticket_by_identifier(db, identifier, current_user)
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    old_priority = ticket.priority
    if _enum_str(old_priority) == _enum_str(new_priority):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Ticket already has priority {_enum_str(new_priority)}",
        )

    ticket.priority = new_priority

    actor = (
        responsible_user
        or getattr(current_user, "username", None)
        or getattr(current_user, "full_name", None)
        or "system"
    )
    create_change_audit(
        db=db,
        ticket_id=ticket.id,
        funcionario_id=getattr(current_user, "id", None),
        responsible_user=actor,
        event_type="PRIORITY_CHANGE",
        modified_field="priority",
        old_value=_enum_str(old_priority),
        new_value=_enum_str(new_priority),
        change_reason=change_reason or "Modificación manual de prioridad",
    )

    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket_detail(
    db: Session,
    identifier: str,
    current_user,
) -> TicketDetailResponse:
    """Obtiene detalle completo de PQRS con solicitante, IA, SLA y línea de tiempo (HU-16)."""
    ticket = get_ticket_by_identifier(db, identifier, current_user, load_relations=True)
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")

    ai_records: list[AIAudit] = list(getattr(ticket, "ai_audits", None) or [])
    if not ai_records and getattr(ticket, "ai_audit", None) is not None:
        ai_records = [ticket.ai_audit]
    ai_records.sort(key=lambda item: _normalize_dt(item.created_at))

    latest_ai = ai_records[-1] if ai_records else None
    clasificacion_ia = (
        AIAuditSummaryOut(
            id=latest_ai.id,
            ai_model=latest_ai.ai_model,
            provider=latest_ai.provider,
            classification_source=latest_ai.classification_source,
            suggested_type=_enum_str(latest_ai.suggested_type),
            suggested_priority=_enum_str(latest_ai.suggested_priority),
            suggested_area_code=latest_ai.suggested_area_code,
            decision_justification=latest_ai.decision_justification,
            confidence=latest_ai.confidence,
            created_at=latest_ai.created_at,
        )
        if latest_ai is not None
        else None
    )

    alert_level, days_remaining, is_overdue = _compute_sla_state(
        ticket.due_date,
        ticket.status,
    )
    sla_detail = TicketSLADetailOut(
        filing_date=ticket.filing_date,
        due_date=ticket.due_date,
        needs_sla_validation=ticket.needs_sla_validation,
        alert_level=alert_level,
        days_remaining=days_remaining,
        is_overdue=is_overdue,
    )

    timeline: list[TimelineEventOut] = []
    for ai_item in ai_records:
        timeline.append(
            TimelineEventOut(
                event_id=ai_item.id,
                source_type="AI_DECISION",
                visual_badge="IA",
                timestamp=ai_item.created_at,
                actor=f"IA ({ai_item.provider}/{ai_item.ai_model})",
                actor_id=None,
                title=f"Clasificación automática ({ai_item.classification_source})",
                description=ai_item.decision_justification,
                modified_field=None,
                old_value=None,
                new_value=(
                    f"tipo={_enum_str(ai_item.suggested_type)}, "
                    f"prioridad={_enum_str(ai_item.suggested_priority)}, "
                    f"area={ai_item.suggested_area_code}"
                ),
                details={
                    "modelo": ai_item.ai_model,
                    "proveedor": ai_item.provider,
                    "fuente": ai_item.classification_source,
                    "confianza": ai_item.confidence,
                },
            )
        )

    change_records: list[ChangeAudit] = list(getattr(ticket, "change_audits", None) or [])
    for ch in change_records:
        func_obj = getattr(ch, "funcionario", None)
        actor_label = (
            getattr(func_obj, "full_name", None)
            or getattr(func_obj, "username", None)
            or ch.responsible_user
        )
        timeline.append(
            TimelineEventOut(
                event_id=ch.id,
                source_type="HUMAN_INTERVENTION",
                visual_badge="HUMANO",
                timestamp=ch.created_at,
                actor=actor_label,
                actor_id=getattr(ch, "funcionario_id", None),
                title=f"Intervención manual: {ch.event_type}",
                description=ch.change_reason or f"Modificación de {ch.modified_field}",
                modified_field=ch.modified_field,
                old_value=ch.old_value,
                new_value=ch.new_value,
                details={
                    "responsible_user": ch.responsible_user,
                    "event_type": ch.event_type,
                },
            )
        )

    timeline.sort(key=lambda ev: _normalize_dt(ev.timestamp))

    return TicketDetailResponse(
        id=ticket.id,
        tracking_number=ticket.tracking_number,
        original_text=ticket.original_text,
        ticket_type=ticket.ticket_type,
        priority=ticket.priority,
        status=_enum_str(ticket.status),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        claimant=ClaimantDetailOut.model_validate(ticket.claimant),
        area=AreaOut.model_validate(ticket.area) if ticket.area is not None else None,
        sla=sla_detail,
        clasificacion_ia=clasificacion_ia,
        justificacion_ia=latest_ai.decision_justification if latest_ai else None,
        timeline=timeline,
    )
