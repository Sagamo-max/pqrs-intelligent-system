import httpx
import pytest

from app.core.config import settings
from app.models.ticket import Ticket
from app.services.companero_client import send_pqr_to_companero


def _create_ticket(
    client,
    sample_ticket_payload,
    seed_areas,
    mock_openai_classification,
):
    mock_openai_classification()
    response = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    assert response.status_code == 201
    return response


def _configure_companero(mocker, *, enabled=True, url="https://companero.test", key="test-key"):
    mocker.patch.object(settings, "COMPANERO_API_ENABLED", enabled)
    mocker.patch.object(settings, "COMPANERO_API_URL", url)
    mocker.patch.object(settings, "COMPANERO_API_KEY", key)


@pytest.mark.integration
def test_send_pqr_disabled(
    client,
    sample_ticket_payload,
    seed_areas,
    mock_openai_classification,
    db_session,
    mocker,
):
    mocker.patch.object(settings, "COMPANERO_API_ENABLED", False)
    mocker.patch("app.services.companero_client.httpx.Client")
    response = _create_ticket(client, sample_ticket_payload, seed_areas, mock_openai_classification)
    ticket = db_session.query(Ticket).filter_by(
        tracking_number=response.json()["tracking_number"]
    ).one()

    assert send_pqr_to_companero(db_session, ticket) is False


@pytest.mark.integration
def test_send_pqr_missing_credentials(db_session, mocker):
    _configure_companero(mocker, enabled=True, url="", key="")
    post = mocker.patch("app.services.companero_client.httpx.Client")

    assert send_pqr_to_companero(db_session, Ticket(tracking_number="PQRS-TEST")) is False
    post.assert_not_called()


@pytest.mark.integration
def test_send_pqr_success(
    client, sample_ticket_payload, seed_areas, mock_openai_classification, db_session, mocker
):
    response = _create_ticket(client, sample_ticket_payload, seed_areas, mock_openai_classification)
    ticket = db_session.query(Ticket).filter_by(
        tracking_number=response.json()["tracking_number"]
    ).one()
    _configure_companero(mocker)
    http_client = mocker.MagicMock()
    http_client.post.return_value.status_code = 202
    mocker.patch("app.services.companero_client.httpx.Client").return_value.__enter__.return_value = http_client

    assert send_pqr_to_companero(db_session, ticket) is True
    request = http_client.post.call_args
    assert request.args[0] == "https://companero.test/api/v1/intake/pqr"
    assert request.kwargs["headers"]["X-API-Key"] == "test-key"
    assert request.kwargs["json"]["text"] == ticket.ai_audit.sanitized_text
    assert request.kwargs["json"]["client_name"] == "Juan Perez"
    assert request.kwargs["json"]["external_reference"] == ticket.tracking_number


@pytest.mark.integration
def test_send_pqr_http_error(
    client, sample_ticket_payload, seed_areas, mock_openai_classification, db_session, mocker
):
    response = _create_ticket(client, sample_ticket_payload, seed_areas, mock_openai_classification)
    ticket = db_session.query(Ticket).filter_by(
        tracking_number=response.json()["tracking_number"]
    ).one()
    _configure_companero(mocker)
    request = httpx.Request("POST", "https://companero.test/api/v1/intake/pqr")
    response = httpx.Response(500, request=request, text="failure")
    http_client = mocker.MagicMock()
    http_client.post.return_value = response
    mocker.patch("app.services.companero_client.httpx.Client").return_value.__enter__.return_value = http_client

    assert send_pqr_to_companero(db_session, ticket) is False


@pytest.mark.integration
def test_send_pqr_network_error(
    client, sample_ticket_payload, seed_areas, mock_openai_classification, db_session, mocker
):
    response = _create_ticket(client, sample_ticket_payload, seed_areas, mock_openai_classification)
    ticket = db_session.query(Ticket).filter_by(
        tracking_number=response.json()["tracking_number"]
    ).one()
    _configure_companero(mocker)
    http_client = mocker.MagicMock()
    http_client.post.side_effect = httpx.RequestError(
        "network failure",
        request=httpx.Request("POST", "https://companero.test/api/v1/intake/pqr"),
    )
    mocker.patch("app.services.companero_client.httpx.Client").return_value.__enter__.return_value = http_client

    assert send_pqr_to_companero(db_session, ticket) is False


@pytest.mark.integration
def test_create_ticket_with_companero_enabled(
    client, sample_ticket_payload, seed_areas, mock_openai_classification, mocker
):
    _configure_companero(mocker)
    http_client = mocker.MagicMock()
    http_client.post.return_value.status_code = 202
    post = mocker.patch("app.services.companero_client.httpx.Client")
    post.return_value.__enter__.return_value = http_client

    response = _create_ticket(client, sample_ticket_payload, seed_areas, mock_openai_classification)

    assert response.status_code == 201
    http_client.post.assert_called_once()


@pytest.mark.integration
def test_create_ticket_survives_companero_failure(
    client, sample_ticket_payload, seed_areas, mock_openai_classification, db_session, mocker
):
    _configure_companero(mocker)
    http_client = mocker.MagicMock()
    http_client.post.side_effect = httpx.RequestError(
        "network failure",
        request=httpx.Request("POST", "https://companero.test/api/v1/intake/pqr"),
    )
    post = mocker.patch("app.services.companero_client.httpx.Client")
    post.return_value.__enter__.return_value = http_client

    response = _create_ticket(client, sample_ticket_payload, seed_areas, mock_openai_classification)

    assert response.status_code == 201
    assert db_session.query(Ticket).count() == 1
