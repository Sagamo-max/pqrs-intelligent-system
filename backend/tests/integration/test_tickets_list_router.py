from datetime import datetime, timezone

import pytest

from app.models.area import Area
from app.models.claimant import Claimant
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketType


def _create_ticket(
    db_session,
    suffix,
    *,
    area_id=None,
    priority=TicketPriority.MEDIUM,
    status=TicketStatus.RECEIVED,
):
    claimant = Claimant(
        document_type="CC",
        document_number=f"list-{suffix}",
        first_name="List",
        last_name="Test",
        email=f"list-{suffix}@example.com",
    )
    db_session.add(claimant)
    db_session.flush()
    ticket = Ticket(
        claimant_id=claimant.id,
        area_id=area_id,
        tracking_number=f"LIST-{suffix}",
        original_text="Texto de prueba para listado de tickets.",
        ticket_type=TicketType.PETITION,
        priority=priority,
        status=status,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(ticket)
    db_session.flush()
    return ticket


@pytest.mark.integration
def test_list_tickets_empty(client):
    response = client.get("/api/v1/pqrs/")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }


@pytest.mark.integration
def test_list_tickets_pagination(client, db_session):
    for index in range(5):
        _create_ticket(db_session, f"page-{index}")

    response = client.get("/api/v1/pqrs/?limit=2")
    data = response.json()

    assert response.status_code == 200
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0


@pytest.mark.integration
def test_list_tickets_filter_by_status(client, db_session):
    _create_ticket(db_session, "received", status=TicketStatus.RECEIVED)
    _create_ticket(db_session, "resolved", status=TicketStatus.RESOLVED)

    response = client.get("/api/v1/pqrs/?status=RESOLVED")
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 1
    assert data["items"][0]["status"] == "RESOLVED"


@pytest.mark.integration
def test_list_tickets_filter_by_area(client, db_session, seed_areas):
    _create_ticket(db_session, "area-a", area_id=seed_areas[0].id)
    _create_ticket(db_session, "area-b", area_id=seed_areas[1].id)

    response = client.get(
        f"/api/v1/pqrs/?area_id={seed_areas[0].id}"
    )
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 1
    assert data["items"][0]["area"]["id"] == str(seed_areas[0].id)


@pytest.mark.integration
def test_list_tickets_filter_by_priority(client, db_session):
    _create_ticket(db_session, "high", priority=TicketPriority.HIGH)
    _create_ticket(db_session, "low", priority=TicketPriority.LOW)

    response = client.get("/api/v1/pqrs/?priority=HIGH")
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 1
    assert data["items"][0]["priority"] == "HIGH"


@pytest.mark.integration
def test_list_tickets_requires_auth(auth_client):
    response = auth_client.get("/api/v1/pqrs/")

    assert response.status_code == 401
