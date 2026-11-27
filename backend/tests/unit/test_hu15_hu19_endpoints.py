import os
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

# Garantizar variables mínimas de Settings para pruebas unitarias aisladas (sin DB real)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("AI_MODEL_NAME", "gpt-6-luna")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-jwt-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "unit-test-refresh-secret")

from fastapi.testclient import TestClient

from app.core.auth_deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.area import Area
from app.models.audit import AIAudit, ChangeAudit
from app.models.claimant import Claimant
from app.models.funcionario import Funcionario, FuncionarioRole
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketType
from app.schemas.classification import AreaCode, TicketClassification
from app.services.audit_service import create_ai_audit
from app.services.classifier import ClassificationOutcome


def _make_user(role: FuncionarioRole = FuncionarioRole.MASTER, area_id=None) -> Funcionario:
    return Funcionario(
        id=uuid4(),
        username=f"user_{role.value.lower()}",
        hashed_password="x",
        full_name=f"Funcionario {role.value}",
        role=role,
        area_id=area_id,
        is_active=True,
    )


def _make_area(code: str = "ATENCION_USUARIO", name: str = "Atención al Usuario", is_active: bool = True) -> Area:
    return Area(
        id=uuid4(),
        code=code,
        name=name,
        description="Área de prueba",
        is_active=is_active,
        is_default=(code == "ATENCION_USUARIO"),
    )


def _make_claimant() -> Claimant:
    return Claimant(
        id=uuid4(),
        document_type="CC",
        document_number="1000000001",
        first_name="Camila",
        last_name="Rojas",
        email="camila.rojas@ejemplo.co",
        phone="3000000001",
    )


def _make_ticket(area: Area | None = None, claimant: Claimant | None = None) -> Ticket:
    now = datetime.now(timezone.utc)
    filing = date.today()
    due = filing + timedelta(days=15)
    ticket_id = uuid4()
    t = Ticket(
        id=ticket_id,
        claimant_id=claimant.id if claimant else uuid4(),
        area_id=area.id if area else None,
        tracking_number="PQRS-UNIT0001",
        original_text="Solicito información sobre el estado de mi trámite de radicación.",
        ticket_type=TicketType.PETITION,
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.RECEIVED,
        filing_date=filing,
        due_date=due,
        needs_sla_validation=False,
        created_at=now,
        updated_at=now,
    )
    t.area = area
    t.claimant = claimant
    t.ai_audits = []
    t.change_audits = []
    return t


@pytest.fixture
def unit_client():
    mock_db = MagicMock()
    current_user_holder = {"user": _make_user(FuncionarioRole.MASTER)}

    def override_get_db():
        yield mock_db

    def override_get_current_user():
        return current_user_holder["user"]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client, mock_db, current_user_holder

    app.dependency_overrides.clear()


# =====================================================================
# HU-15 — Reasignación manual de área responsable
# =====================================================================


@pytest.mark.unit
def test_hu15_reassign_area_success_keeps_status_and_sla(unit_client):
    client, mock_db, holder = unit_client
    old_area = _make_area("ATENCION_USUARIO", "Atención al Usuario")
    new_area = _make_area("FACTURACION", "Facturación")
    ticket = _make_ticket(area=old_area)
    original_status = ticket.status
    original_due_date = ticket.due_date
    original_sla_flag = ticket.needs_sla_validation

    mock_db.scalar.side_effect = [ticket, new_area]

    def _refresh(obj):
        if obj is ticket:
            obj.area = new_area

    mock_db.refresh.side_effect = _refresh

    resp = client.patch(
        f"/api/pqrs/{ticket.id}/area",
        json={
            "id_area": str(new_area.id),
            "motivo": "Corresponde a facturación",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["area"]["code"] == "FACTURACION"
    assert body["status"] == original_status.value
    assert body["due_date"] == original_due_date.isoformat()
    assert body["needs_sla_validation"] is original_sla_flag

    assert ticket.area_id == new_area.id
    assert ticket.status == original_status
    assert ticket.due_date == original_due_date

    added_audits = [
        call.args[0]
        for call in mock_db.add.call_args_list
        if isinstance(call.args[0], ChangeAudit)
    ]
    assert len(added_audits) == 1
    audit = added_audits[0]
    assert audit.ticket_id == ticket.id
    assert audit.funcionario_id == holder["user"].id
    assert audit.modified_field == "area_id"
    assert audit.old_value == "ATENCION_USUARIO"
    assert audit.new_value == "FACTURACION"
    mock_db.commit.assert_called_once()


@pytest.mark.unit
def test_hu15_reassign_area_ticket_not_found(unit_client):
    client, mock_db, _ = unit_client
    mock_db.scalar.return_value = None

    resp = client.patch(
        f"/api/pqrs/{uuid4()}/area",
        json={"area_id": str(uuid4())},
    )
    assert resp.status_code == 404


@pytest.mark.unit
def test_hu15_reassign_area_not_found(unit_client):
    client, mock_db, _ = unit_client
    ticket = _make_ticket(area=_make_area())
    mock_db.scalar.side_effect = [ticket, None]

    resp = client.patch(
        f"/api/pqrs/{ticket.id}/area",
        json={"area_id": str(uuid4())},
    )
    assert resp.status_code == 404


@pytest.mark.unit
def test_hu15_reassign_area_inactive_returns_400(unit_client):
    client, mock_db, _ = unit_client
    ticket = _make_ticket(area=_make_area())
    inactive_area = _make_area("ARCHIVO", "Archivo Inactivo", is_active=False)
    mock_db.scalar.side_effect = [ticket, inactive_area]

    resp = client.patch(
        f"/api/pqrs/{ticket.id}/area",
        json={"area_id": str(inactive_area.id)},
    )
    assert resp.status_code == 400


@pytest.mark.unit
def test_hu15_reassign_same_area_returns_400(unit_client):
    client, mock_db, _ = unit_client
    area = _make_area("FACTURACION", "Facturación")
    ticket = _make_ticket(area=area)
    mock_db.scalar.side_effect = [ticket, area]

    resp = client.patch(
        f"/api/pqrs/{ticket.id}/area",
        json={"area_id": str(area.id)},
    )
    assert resp.status_code == 400


# =====================================================================
# HU-16 — Detalle y seguimiento individual de PQRS
# =====================================================================


@pytest.mark.unit
def test_hu16_get_ticket_detail_timeline_chronological_and_distinguished(unit_client):
    client, mock_db, _ = unit_client
    area = _make_area("FACTURACION", "Facturación")
    claimant = _make_claimant()
    ticket = _make_ticket(area=area, claimant=claimant)
    ticket.ticket_type = TicketType.CLAIM
    ticket.priority = TicketPriority.HIGH

    t0 = datetime(2026, 11, 20, 10, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 11, 21, 9, 30, 0, tzinfo=timezone.utc)

    ai_audit = AIAudit(
        id=uuid4(),
        ticket_id=ticket.id,
        ai_model="gpt-6-luna",
        provider="openai",
        original_text=ticket.original_text,
        sanitized_text=ticket.original_text,
        decision_justification="Cobro duplicado detectado en factura mensual.",
        suggested_type=TicketType.CLAIM,
        suggested_priority=TicketPriority.HIGH,
        suggested_area_code="FACTURACION",
        classification_source="openai",
        confidence=0.95,
        raw_response={"id": "resp-1"},
        created_at=t0,
    )
    func_user = _make_user(FuncionarioRole.SUPERVISOR)
    ch_older = ChangeAudit(
        id=uuid4(),
        ticket_id=ticket.id,
        funcionario_id=func_user.id,
        responsible_user=func_user.username,
        event_type="AREA_REASSIGNMENT",
        modified_field="area_id",
        old_value="ATENCION_USUARIO",
        new_value="FACTURACION",
        change_reason="Reasignado a facturación",
        created_at=t1,
    )
    ch_older.funcionario = func_user

    ch_newer = ChangeAudit(
        id=uuid4(),
        ticket_id=ticket.id,
        funcionario_id=func_user.id,
        responsible_user=func_user.username,
        event_type="PRIORITY_CHANGE",
        modified_field="priority",
        old_value="MEDIUM",
        new_value="HIGH",
        change_reason="Escalamiento prioritario",
        created_at=t2,
    )
    ch_newer.funcionario = func_user

    ticket.ai_audits = [ai_audit]
    # Insertar desordenados intencionalmente para verificar ordenamiento cronológico
    ticket.change_audits = [ch_newer, ch_older]

    mock_db.scalar.return_value = ticket

    resp = client.get(f"/api/pqrs/{ticket.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["tracking_number"] == ticket.tracking_number
    assert data["claimant"]["email"] == claimant.email
    assert data["original_text"] == ticket.original_text
    assert data["justificacion_ia"] == ai_audit.decision_justification
    assert data["clasificacion_ia"]["suggested_area_code"] == "FACTURACION"
    assert data["sla"]["filing_date"] == ticket.filing_date.isoformat()

    timeline = data["timeline"]
    assert len(timeline) == 3
    assert [ev["event_id"] for ev in timeline] == [
        str(ai_audit.id),
        str(ch_older.id),
        str(ch_newer.id),
    ]
    assert timeline[0]["source_type"] == "AI_DECISION"
    assert timeline[0]["visual_badge"] == "IA"
    assert timeline[1]["source_type"] == "HUMAN_INTERVENTION"
    assert timeline[1]["visual_badge"] == "HUMANO"
    assert timeline[1]["actor"] == func_user.full_name
    assert timeline[2]["visual_badge"] == "HUMANO"


@pytest.mark.unit
def test_hu16_get_ticket_detail_not_found(unit_client):
    client, mock_db, _ = unit_client
    mock_db.scalar.return_value = None

    resp = client.get(f"/api/pqrs/{uuid4()}")
    assert resp.status_code == 404


# =====================================================================
# HU-17 — Auditoría de decisión IA
# =====================================================================


@pytest.mark.unit
def test_hu17_create_ai_audit_persists_raw_json_justification_and_model():
    mock_db = MagicMock()
    ticket_id = uuid4()
    outcome = ClassificationOutcome(
        classification=TicketClassification(
            ticket_type=TicketType.COMPLAINT,
            priority=TicketPriority.MEDIUM,
            responsible_area=AreaCode.ATENCION_USUARIO,
            decision_justification="Queja por trato inadecuado en ventanilla presencial.",
        ),
        source="openai",
        raw_response={"id": "chatcmpl-123", "model": "gpt-6-luna"},
        tokens_used=140,
        latency_ms=250,
        confidence=0.92,
    )

    audit = create_ai_audit(
        db=mock_db,
        ticket_id=ticket_id,
        outcome=outcome,
        original_text="Texto original",
        sanitized_text="Texto sanitizado",
    )

    mock_db.add.assert_called_once_with(audit)
    mock_db.flush.assert_called_once()
    assert audit.ticket_id == ticket_id
    assert audit.raw_response == {"id": "chatcmpl-123", "model": "gpt-6-luna"}
    assert audit.decision_justification == "Queja por trato inadecuado en ventanilla presencial."
    assert audit.ai_model == "gpt-6-luna"


@pytest.mark.unit
def test_hu17_get_ai_audit_history_supervisor_success(unit_client):
    client, mock_db, holder = unit_client
    holder["user"] = _make_user(FuncionarioRole.SUPERVISOR)
    ticket = _make_ticket(area=_make_area())

    now = datetime.now(timezone.utc)
    a1 = AIAudit(
        id=uuid4(),
        ticket_id=ticket.id,
        ai_model="gpt-6-luna",
        provider="openai",
        original_text=ticket.original_text,
        sanitized_text=ticket.original_text,
        decision_justification="Primera clasificación automática.",
        suggested_type=TicketType.PETITION,
        suggested_priority=TicketPriority.LOW,
        suggested_area_code="ATENCION_USUARIO",
        classification_source="openai",
        raw_response={"run": 1},
        created_at=now,
    )
    a2 = AIAudit(
        id=uuid4(),
        ticket_id=ticket.id,
        ai_model="gpt-6-luna",
        provider="openai",
        original_text=ticket.original_text,
        sanitized_text=ticket.original_text,
        decision_justification="Segunda evaluación de auditoría IA.",
        suggested_type=TicketType.CLAIM,
        suggested_priority=TicketPriority.HIGH,
        suggested_area_code="FACTURACION",
        classification_source="openai",
        raw_response={"run": 2},
        created_at=now + timedelta(minutes=5),
    )

    mock_db.scalar.return_value = ticket
    mock_db.scalars.return_value.all.return_value = [a1, a2]

    resp = client.get(f"/api/pqrs/{ticket.id}/auditoria-ia")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["raw_response"] == {"run": 1}
    assert body[1]["decision_justification"] == "Segunda evaluación de auditoría IA."


@pytest.mark.unit
def test_hu17_get_ai_audit_history_forbidden_for_analista(unit_client):
    client, _, holder = unit_client
    holder["user"] = _make_user(FuncionarioRole.ANALISTA, area_id=uuid4())

    resp = client.get(f"/api/pqrs/{uuid4()}/auditoria-ia")
    assert resp.status_code == 403


@pytest.mark.unit
def test_hu17_get_ai_audit_history_ticket_not_found(unit_client):
    client, mock_db, holder = unit_client
    holder["user"] = _make_user(FuncionarioRole.MASTER)
    mock_db.scalar.return_value = None

    resp = client.get(f"/api/pqrs/{uuid4()}/auditoria-ia")
    assert resp.status_code == 404


# =====================================================================
# HU-18 — Auditoría de intervenciones humanas
# =====================================================================


@pytest.mark.unit
def test_hu18_change_priority_success_registers_change_audit(unit_client):
    client, mock_db, holder = unit_client
    area = _make_area("SOPORTE_TECNICO", "Soporte Técnico")
    ticket = _make_ticket(area=area)
    original_due = ticket.due_date
    original_status = ticket.status

    mock_db.scalar.return_value = ticket

    resp = client.patch(
        f"/api/pqrs/{ticket.id}/prioridad",
        json={
            "priority": "HIGH",
            "change_reason": "Servicio crítico interrumpido",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["priority"] == "HIGH"
    assert body["due_date"] == original_due.isoformat()
    assert body["status"] == original_status.value

    added_audits = [
        call.args[0]
        for call in mock_db.add.call_args_list
        if isinstance(call.args[0], ChangeAudit)
    ]
    assert len(added_audits) == 1
    audit = added_audits[0]
    assert audit.funcionario_id == holder["user"].id
    assert audit.modified_field == "priority"
    assert audit.old_value == "MEDIUM"
    assert audit.new_value == "HIGH"
    mock_db.commit.assert_called_once()


@pytest.mark.unit
def test_hu18_change_priority_same_returns_400(unit_client):
    client, mock_db, _ = unit_client
    ticket = _make_ticket(area=_make_area())
    ticket.priority = TicketPriority.MEDIUM
    mock_db.scalar.return_value = ticket

    resp = client.patch(
        f"/api/pqrs/{ticket.id}/prioridad",
        json={"priority": "MEDIUM"},
    )
    assert resp.status_code == 400


@pytest.mark.unit
def test_hu18_change_ticket_type_registers_funcionario_id(unit_client):
    client, mock_db, holder = unit_client
    ticket = _make_ticket(area=_make_area())
    ticket.ticket_type = TicketType.PETITION
    mock_db.scalar.return_value = ticket

    resp = client.patch(
        f"/api/pqrs/{ticket.tracking_number}/tipo",
        json={
            "ticket_type": "CONSULTATION",
            "responsible_user": "supervisor.legal",
            "change_reason": "Consulta normativa compleja",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ticket_type"] == "CONSULTATION"
    assert body["due_date"] is None
    assert body["needs_sla_validation"] is True

    added_audits = [
        call.args[0]
        for call in mock_db.add.call_args_list
        if isinstance(call.args[0], ChangeAudit)
    ]
    assert len(added_audits) == 1
    assert added_audits[0].funcionario_id == holder["user"].id
    assert added_audits[0].modified_field == "ticket_type"


# =====================================================================
# HU-19 — Dashboard de métricas básicas
# =====================================================================


@pytest.mark.unit
def test_hu19_dashboard_metrics_success(unit_client):
    client, mock_db, _ = unit_client
    area_id_1 = uuid4()
    area_id_2 = uuid4()

    res_tipo = MagicMock()
    res_tipo.all.return_value = [
        (TicketType.PETITION, 4),
        (TicketType.COMPLAINT, 2),
        (TicketType.CLAIM, 3),
        (TicketType.SUGGESTION, 1),
    ]
    res_area = MagicMock()
    res_area.all.return_value = [
        (area_id_1, "FACTURACION", "Facturación", 6),
        (area_id_2, "ATENCION_USUARIO", "Atención al Usuario", 4),
    ]
    res_prio = MagicMock()
    res_prio.all.return_value = [
        (TicketPriority.HIGH, 3),
        (TicketPriority.MEDIUM, 5),
        (TicketPriority.LOW, 2),
    ]
    res_sla = MagicMock()
    res_sla.one.return_value = SimpleNamespace(
        total=10,
        vencidas=2,
        sin_fecha_sla=1,
        a_tiempo=7,
    )

    mock_db.execute.side_effect = [res_tipo, res_area, res_prio, res_sla]

    resp = client.get("/api/dashboard/metricas")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_pqrs"] == 10
    assert data["por_tipo"] == {
        "PETITION": 4,
        "COMPLAINT": 2,
        "CLAIM": 3,
        "SUGGESTION": 1,
    }
    assert len(data["por_area"]) == 2
    assert data["por_prioridad"] == {"HIGH": 3, "MEDIUM": 5, "LOW": 2}
    assert data["cumplimiento_sla"]["vencidas"] == 2
    assert data["cumplimiento_sla"]["a_tiempo"] == 7
    assert data["cumplimiento_sla"]["sin_fecha_sla"] == 1
    assert data["cumplimiento_sla"]["porcentaje_a_tiempo"] == 77.78


@pytest.mark.unit
def test_hu19_dashboard_metrics_empty_db_no_division_by_zero(unit_client):
    client, mock_db, _ = unit_client

    res_empty = MagicMock()
    res_empty.all.return_value = []
    res_sla = MagicMock()
    res_sla.one.return_value = SimpleNamespace(
        total=0,
        vencidas=0,
        sin_fecha_sla=0,
        a_tiempo=0,
    )
    mock_db.execute.side_effect = [res_empty, res_empty, res_empty, res_sla]

    resp = client.get("/api/dashboard/metricas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_pqrs"] == 0
    assert data["cumplimiento_sla"]["porcentaje_a_tiempo"] == 0.0


@pytest.mark.unit
def test_hu19_dashboard_metrics_analista_filters_by_area(unit_client):
    client, mock_db, holder = unit_client
    analista_area_id = uuid4()
    holder["user"] = _make_user(FuncionarioRole.ANALISTA, area_id=analista_area_id)

    res_empty = MagicMock()
    res_empty.all.return_value = []
    res_sla = MagicMock()
    res_sla.one.return_value = SimpleNamespace(
        total=0,
        vencidas=0,
        sin_fecha_sla=0,
        a_tiempo=0,
    )
    mock_db.execute.side_effect = [res_empty, res_empty, res_empty, res_sla]

    resp = client.get("/api/dashboard/metricas")
    assert resp.status_code == 200
    assert mock_db.execute.call_count == 4
    first_stmt = mock_db.execute.call_args_list[0].args[0]
    assert "area_id" in str(first_stmt)
