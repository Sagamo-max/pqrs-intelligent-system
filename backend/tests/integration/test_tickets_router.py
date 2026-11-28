import pytest
from app.models.ticket import Ticket
from app.models.audit import AIAudit
from app.models.audit_attempt import AIAuditAttempt
from app.models.claimant import Claimant
from app.models.ticket import TicketPriority, TicketType
from app.schemas.classification import AreaCode, TicketClassification
from app.services.classifier import (
    AttemptInfo,
    ClassificationOutcome,
    FALLBACK_CLASSIFICATION,
)

@pytest.mark.integration
def test_receive_pqrs_success(client, seed_areas, sample_ticket_payload, mock_openai_classification, db_session):
    mock_openai_classification()
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "tracking_number" in data
    assert data["status"] == "RECEIVED"
    
    ticket = db_session.query(Ticket).filter_by(tracking_number=data["tracking_number"]).first()
    assert ticket is not None
    assert ticket.ticket_type == "PETITION"
    
    audit = db_session.query(AIAudit).filter_by(ticket_id=ticket.id).first()
    assert audit is not None
    assert audit.decision_justification.startswith("Mocked justification")

@pytest.mark.integration
def test_receive_pqrs_short_text(client, sample_ticket_payload):
    sample_ticket_payload["free_text"] = "corto"
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    assert response.status_code == 422

@pytest.mark.integration
def test_receive_pqrs_invalid_email(client, sample_ticket_payload):
    sample_ticket_payload["claimant"]["email"] = "no-es-correo"
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    assert response.status_code == 422

@pytest.mark.integration
def test_reuse_claimant(client, seed_areas, sample_ticket_payload, mock_openai_classification, db_session):
    mock_openai_classification()
    
    client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    count_before = db_session.query(Claimant).count()
    
    sample_ticket_payload["free_text"] = "Otro texto suficientemente largo"
    client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    count_after = db_session.query(Claimant).count()
    
    assert count_before == count_after

@pytest.mark.integration
def test_ticket_creation_is_atomic(client, sample_ticket_payload, seed_areas, mocker, db_session):
    mocker.patch("app.services.ticket_service.classify_ticket_text", return_value=ClassificationOutcome(
        classification=FALLBACK_CLASSIFICATION,
        source="fallback",
        raw_response=None,
        tokens_used=None,
        latency_ms=None,
        confidence=None
    ))
    mocker.patch("app.services.ticket_service.create_ai_audit", side_effect=Exception("DB failure"))
    
    try:
        client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    except Exception:
        pass
    
    assert db_session.query(Ticket).count() == 0

@pytest.mark.integration
def test_ai_fallback_never_breaks_flow(client, sample_ticket_payload, seed_areas, mocker):
    mocker.patch("app.services.classifier._call_openai_with_retry", side_effect=Exception("OpenAI down"))
    
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    assert response.status_code == 201
    assert response.json()["area"]["code"] == "ATENCION_USUARIO"

@pytest.mark.integration
def test_ticket_response_accepts_uuid(client, sample_ticket_payload, mock_openai_classification, seed_areas):
    mock_openai_classification()
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    assert response.status_code == 201
    assert "tracking_number" in response.json()


@pytest.mark.integration
def test_heuristic_used_when_openai_fails(
    client, sample_ticket_payload, seed_areas, mocker, db_session
):
    classification = TicketClassification(
        ticket_type=TicketType.PETITION,
        priority=TicketPriority.MEDIUM,
        responsible_area=AreaCode.FACTURACION,
        decision_justification="Clasificación heurística para facturación.",
    )
    outcome = ClassificationOutcome(classification=classification, source="heuristic")
    mocker.patch("app.services.ticket_service.classify_ticket_text", return_value=outcome)

    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 201
    ticket = db_session.query(Ticket).filter_by(
        tracking_number=response.json()["tracking_number"]
    ).one()
    audit = db_session.query(AIAudit).filter_by(ticket_id=ticket.id).one()
    assert audit.classification_source == "heuristic"


@pytest.mark.integration
def test_audit_attempts_persisted(
    client, sample_ticket_payload, seed_areas, mocker, db_session
):
    outcome = ClassificationOutcome(
        classification=FALLBACK_CLASSIFICATION,
        source="fallback",
        attempts=[
            AttemptInfo(1, "APIConnectionError", "first failure", 10),
            AttemptInfo(2, "APIConnectionError", "second failure", 20),
        ],
    )
    mocker.patch("app.services.ticket_service.classify_ticket_text", return_value=outcome)

    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 201
    ticket = db_session.query(Ticket).filter_by(
        tracking_number=response.json()["tracking_number"]
    ).one()
    attempts = db_session.query(AIAuditAttempt).filter_by(ticket_id=ticket.id).all()
    assert len(attempts) == 2


@pytest.mark.integration
def test_receive_pqrs_public_no_auth(
    auth_client, seed_areas, sample_ticket_payload, mock_openai_classification
):
    mock_openai_classification()
    response = auth_client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 201
    data = response.json()
    assert "tracking_number" in data
    assert data["status"] == "RECEIVED"


@pytest.mark.integration
def test_list_pqrs_requires_auth(auth_client):
    response = auth_client.get("/api/v1/pqrs/")
    assert response.status_code == 401


@pytest.mark.integration
def test_receive_pqrs_rate_limit(
    auth_client,
    seed_areas,
    sample_ticket_payload,
    mock_openai_classification,
    monkeypatch,
):
    mock_openai_classification()
    monkeypatch.setenv("PUBLIC_PQRS_RATE_LIMIT_MAX", "2")
    monkeypatch.setenv("PUBLIC_PQRS_RATE_LIMIT_WINDOW_SECONDS", "60")

    first = auth_client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    second = auth_client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    third = auth_client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429
