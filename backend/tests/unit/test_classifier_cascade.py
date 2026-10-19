from unittest.mock import MagicMock

import openai
import pytest

from app.models.ticket import TicketPriority, TicketType
from app.schemas.classification import AreaCode, TicketClassification
from app.services.classifier import (
    ClassificationOutcome,
    classify_ticket_text,
)


def _outcome(source="openai", area=AreaCode.ATENCION_USUARIO):
    return ClassificationOutcome(
        classification=TicketClassification(
            ticket_type=TicketType.PETITION,
            priority=TicketPriority.MEDIUM,
            responsible_area=area,
            decision_justification="Clasificación de prueba suficientemente válida.",
        ),
        source=source,
    )


@pytest.mark.unit
def test_cascade_openai_success(mocker):
    expected = _outcome()
    mocker.patch("app.services.classifier._call_openai_with_retry", return_value=expected)

    assert classify_ticket_text("Texto de prueba") is expected
    assert expected.source == "openai"


@pytest.mark.unit
def test_cascade_heuristic_fallback(mocker):
    mocker.patch(
        "app.services.classifier._call_openai_with_retry",
        side_effect=openai.APIConnectionError(request=MagicMock()),
    )

    outcome = classify_ticket_text("Necesito corregir una factura")

    assert outcome.source == "heuristic"
    assert outcome.classification.responsible_area == AreaCode.FACTURACION


@pytest.mark.unit
def test_cascade_plain_fallback(mocker):
    mocker.patch(
        "app.services.classifier._call_openai_with_retry",
        side_effect=openai.APIConnectionError(request=MagicMock()),
    )

    outcome = classify_ticket_text("Solicito información general sobre mi caso")

    assert outcome.source == "fallback"
    assert outcome.classification.responsible_area == AreaCode.ATENCION_USUARIO


@pytest.mark.unit
def test_cascade_attempts_recorded(mocker):
    mocker.patch(
        "app.services.classifier._call_openai_with_retry",
        side_effect=openai.APIConnectionError(request=MagicMock()),
    )

    outcome = classify_ticket_text("Texto sin palabras clave")

    assert len(outcome.attempts) == 3
    assert [attempt.attempt_number for attempt in outcome.attempts] == [1, 2, 3]
