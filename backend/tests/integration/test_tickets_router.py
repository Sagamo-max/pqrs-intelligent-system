import pytest
from app.models.ticket import Ticket
from app.models.audit import AIAudit
from app.models.claimant import Claimant

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
    mocker.patch("app.services.ticket_service.create_ai_audit", side_effect=Exception("DB failure"))
    
    try:
        client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    except Exception:
        pass
    
    assert db_session.query(Ticket).count() == 0

@pytest.mark.integration
def test_ai_fallback_never_breaks_flow(client, sample_ticket_payload, seed_areas, mocker):
    mocker.patch("app.services.classifier._call_openai", side_effect=Exception("OpenAI down"))
    
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    assert response.status_code == 201
    assert response.json()["area"]["code"] == "ATENCION_USUARIO"

@pytest.mark.integration
def test_ticket_response_accepts_uuid(client, sample_ticket_payload, mock_openai_classification, seed_areas):
    mock_openai_classification()
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    assert response.status_code == 201
    assert "tracking_number" in response.json()

