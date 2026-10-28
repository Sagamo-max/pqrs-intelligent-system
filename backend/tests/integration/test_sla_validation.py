import pytest

from app.models.audit import ChangeAudit
from app.models.ticket import Ticket, TicketType


def _create_ticket(client, payload, mock_openai_classification, ticket_type):
    mock_openai_classification({"ticket_type": ticket_type})
    response = client.post("/api/v1/pqrs/", json=payload)
    assert response.status_code == 201
    return response


def _change_ticket_type(client, tracking_number, ticket_type):
    return client.patch(
        f"/api/v1/pqrs/{tracking_number}/tipo",
        json={
            "ticket_type": ticket_type.value,
            "responsible_user": "funcionario@empresa.com",
            "change_reason": "Verificado manualmente",
        },
    )


@pytest.mark.integration
def test_list_tickets_needs_sla_validation(
    client, seed_areas, sample_ticket_payload, mock_openai_classification
):
    response = _create_ticket(
        client,
        sample_ticket_payload,
        mock_openai_classification,
        TicketType.CONSULTATION,
    )

    ticket_data = response.json()
    assert ticket_data["due_date"] is None
    assert ticket_data["needs_sla_validation"] is True

    filtered = client.get("/api/v1/pqrs/?needs_sla_validation=true")

    assert filtered.status_code == 200
    assert any(
        ticket["tracking_number"] == ticket_data["tracking_number"]
        for ticket in filtered.json()
    )


@pytest.mark.integration
def test_change_ticket_type_recalculates_sla(
    client, seed_areas, sample_ticket_payload, mock_openai_classification
):
    created = _create_ticket(
        client,
        sample_ticket_payload,
        mock_openai_classification,
        TicketType.CONSULTATION,
    )

    response = _change_ticket_type(
        client, created.json()["tracking_number"], TicketType.PETITION
    )

    assert response.status_code == 200
    assert response.json()["ticket_type"] == TicketType.PETITION.value
    assert response.json()["due_date"] is not None
    assert response.json()["needs_sla_validation"] is False


@pytest.mark.integration
def test_change_ticket_type_to_consultation_clears_due_date(
    client, seed_areas, sample_ticket_payload, mock_openai_classification
):
    created = _create_ticket(
        client,
        sample_ticket_payload,
        mock_openai_classification,
        TicketType.PETITION,
    )

    response = _change_ticket_type(
        client, created.json()["tracking_number"], TicketType.CONSULTATION
    )

    assert response.status_code == 200
    assert response.json()["due_date"] is None
    assert response.json()["needs_sla_validation"] is True


@pytest.mark.integration
def test_change_ticket_type_registers_audit(
    client,
    seed_areas,
    sample_ticket_payload,
    mock_openai_classification,
    db_session,
):
    created = _create_ticket(
        client,
        sample_ticket_payload,
        mock_openai_classification,
        TicketType.CONSULTATION,
    )

    response = _change_ticket_type(
        client, created.json()["tracking_number"], TicketType.PETITION
    )

    assert response.status_code == 200
    audit = db_session.query(ChangeAudit).one()
    assert audit.responsible_user == "funcionario@empresa.com"
    assert audit.modified_field == "ticket_type"
    assert audit.old_value == TicketType.CONSULTATION.value
    assert audit.new_value == TicketType.PETITION.value


@pytest.mark.integration
def test_change_ticket_type_same_type_returns_400(
    client, seed_areas, sample_ticket_payload, mock_openai_classification
):
    created = _create_ticket(
        client,
        sample_ticket_payload,
        mock_openai_classification,
        TicketType.PETITION,
    )

    response = _change_ticket_type(
        client, created.json()["tracking_number"], TicketType.PETITION
    )

    assert response.status_code == 400


@pytest.mark.integration
def test_change_ticket_type_unknown_tracking_returns_404(client, seed_areas):
    response = _change_ticket_type(client, "NOEXISTE", TicketType.PETITION)

    assert response.status_code == 404
