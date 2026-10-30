from datetime import date, timedelta

import holidays_co_full
import pytest

from app.models.claimant import Claimant
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketType


def _create_ticket(db_session, suffix, *, due_date, status=TicketStatus.RECEIVED):
    claimant = Claimant(
        document_type="CC",
        document_number=f"alert-{suffix}",
        first_name="Alert",
        last_name="Test",
        email=f"alert-{suffix}@example.com",
    )
    db_session.add(claimant)
    db_session.flush()

    ticket = Ticket(
        claimant_id=claimant.id,
        tracking_number=f"ALERT-{suffix}",
        original_text="Texto de prueba para alertas de vencimiento.",
        ticket_type=TicketType.PETITION,
        priority=TicketPriority.MEDIUM,
        status=status,
        due_date=due_date,
    )
    db_session.add(ticket)
    db_session.flush()
    return ticket


@pytest.mark.integration
def test_alerts_empty(client):
    response = client.get("/api/v1/pqrs/alerts")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_alerts_overdue(client, db_session):
    ticket = _create_ticket(
        db_session,
        "overdue",
        due_date=date.today() - timedelta(days=1),
    )

    response = client.get("/api/v1/pqrs/alerts")

    assert response.status_code == 200
    assert response.json()[0]["tracking_number"] == ticket.tracking_number
    assert response.json()[0]["alert_level"] == "OVERDUE"
    assert response.json()[0]["days_remaining"] == -1


@pytest.mark.integration
def test_alerts_due_soon(client, db_session):
    due_date = holidays_co_full.add_business_days(date.today(), 2)
    ticket = _create_ticket(db_session, "soon", due_date=due_date)

    response = client.get("/api/v1/pqrs/alerts")

    assert response.status_code == 200
    assert response.json()[0]["tracking_number"] == ticket.tracking_number
    assert response.json()[0]["alert_level"] == "DUE_SOON"


@pytest.mark.integration
def test_alerts_normal_excluded(client, db_session):
    due_date = date.today() + timedelta(days=10)
    _create_ticket(db_session, "normal", due_date=due_date)

    response = client.get("/api/v1/pqrs/alerts")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_alerts_resolved_excluded(client, db_session):
    due_date = date.today() - timedelta(days=1)
    _create_ticket(
        db_session,
        "resolved",
        due_date=due_date,
        status=TicketStatus.RESOLVED,
    )

    response = client.get("/api/v1/pqrs/alerts")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_alerts_filter_by_level(client, db_session):
    overdue = _create_ticket(
        db_session,
        "filter-overdue",
        due_date=date.today() - timedelta(days=1),
    )
    _create_ticket(
        db_session,
        "filter-soon",
        due_date=holidays_co_full.add_business_days(date.today(), 2),
    )

    response = client.get("/api/v1/pqrs/alerts?level=OVERDUE")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tracking_number"] == overdue.tracking_number
    assert data[0]["alert_level"] == "OVERDUE"
