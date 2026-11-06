import pytest

from app.models.outbox_event import OutboxEvent
from app.models.ticket import Ticket


@pytest.mark.integration
def test_event_published_on_ticket_creation(
    client, seed_areas, sample_ticket_payload, mock_openai_classification, db_session
):
    mock_openai_classification()

    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 201
    ticket = db_session.query(Ticket).one()
    event = db_session.query(OutboxEvent).one()
    assert event.event_type == "PQRS_CREADA"
    assert event.processed is False
    assert event.payload["ticket"]["ticket_id"] == str(ticket.id)


@pytest.mark.integration
def test_event_payload_structure(
    client, seed_areas, sample_ticket_payload, mock_openai_classification, db_session
):
    mock_openai_classification()

    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 201
    event = db_session.query(OutboxEvent).one()
    payload = event.payload
    assert set(payload) == {
        "event",
        "event_id",
        "timestamp",
        "ticket",
        "claimant",
        "classification",
        "text",
    }
    assert payload["event"] == "PQRS_CREADA"
    assert payload["ticket"]["external_reference"] == payload["ticket"]["tracking_number"]
    assert payload["ticket"]["organization_id"]
    assert payload["classification"]["source"] == "openai"
    assert "original_text" not in payload["text"]
    assert payload["text"]["sanitized"]


@pytest.mark.integration
def test_ticket_stores_organization_id(
    client, seed_areas, sample_ticket_payload, mock_openai_classification, db_session
):
    mock_openai_classification()
    organization_id = sample_ticket_payload["organization_id"]

    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 201
    ticket = db_session.query(Ticket).one()
    assert str(ticket.organization_id) == organization_id


@pytest.mark.integration
def test_event_includes_organization_id(
    client, seed_areas, sample_ticket_payload, mock_openai_classification, db_session
):
    mock_openai_classification()
    organization_id = sample_ticket_payload["organization_id"]

    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 201
    event = db_session.query(OutboxEvent).one()
    assert event.payload["ticket"]["organization_id"] == organization_id


@pytest.mark.integration
def test_event_not_published_on_failure(
    client, seed_areas, sample_ticket_payload, mocker, db_session
):
    mocker.patch(
        "app.services.ticket_service.classify_ticket_text",
        side_effect=RuntimeError("classification failure"),
    )

    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)

    assert response.status_code == 500
    assert db_session.query(OutboxEvent).count() == 0
