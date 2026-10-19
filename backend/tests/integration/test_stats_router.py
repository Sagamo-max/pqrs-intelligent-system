from datetime import datetime, timedelta, timezone

import pytest

from app.models.audit import AIAudit
from app.models.claimant import Claimant
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketType


def _create_audit(db_session, source, suffix, created_at=None):
    claimant = Claimant(
        document_type="CC",
        document_number=f"stats-{suffix}",
        first_name="Stats",
        last_name="Test",
        email=f"stats-{suffix}@example.com",
    )
    db_session.add(claimant)
    db_session.flush()
    ticket = Ticket(
        claimant_id=claimant.id,
        tracking_number=f"STATS-{suffix}",
        original_text="Texto de prueba para estadísticas.",
        ticket_type=TicketType.PETITION,
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.RECEIVED,
        due_date=datetime.now(timezone.utc).date(),
    )
    db_session.add(ticket)
    db_session.flush()
    audit = AIAudit(
        ticket_id=ticket.id,
        ai_model="test-model",
        provider="test",
        original_text=ticket.original_text,
        sanitized_text=ticket.original_text,
        decision_justification="Justificación válida para estadísticas.",
        suggested_type=TicketType.PETITION,
        suggested_priority=TicketPriority.MEDIUM,
        suggested_area_code="ATENCION_USUARIO",
        classification_source=source,
        created_at=created_at,
    )
    db_session.add(audit)
    db_session.flush()
    return audit


@pytest.mark.integration
def test_stats_empty(client):
    response = client.get("/api/v1/pqrs/stats")

    assert response.status_code == 200
    assert response.json() == {
        "last_24h": {"total": 0, "by_source": {"openai": 0, "heuristic": 0, "fallback": 0}},
        "all_time": {"total": 0, "by_source": {"openai": 0, "heuristic": 0, "fallback": 0}},
    }


@pytest.mark.integration
def test_stats_with_audits(client, db_session):
    _create_audit(db_session, "openai", "openai")
    _create_audit(db_session, "heuristic", "heuristic")
    _create_audit(db_session, "fallback", "fallback")

    response = client.get("/api/v1/pqrs/stats")

    assert response.status_code == 200
    assert response.json()["all_time"] == {
        "total": 3,
        "by_source": {"openai": 1, "heuristic": 1, "fallback": 1},
    }


@pytest.mark.integration
def test_stats_last_24h_filters_old(client, db_session):
    _create_audit(
        db_session,
        "fallback",
        "old",
        datetime.now(timezone.utc) - timedelta(hours=48),
    )
    _create_audit(db_session, "openai", "recent")

    response = client.get("/api/v1/pqrs/stats")
    data = response.json()

    assert response.status_code == 200
    assert data["last_24h"] == {
        "total": 1,
        "by_source": {"openai": 1, "heuristic": 0, "fallback": 0},
    }
    assert data["all_time"]["total"] == 2
