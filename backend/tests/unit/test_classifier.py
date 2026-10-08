import pytest
from unittest.mock import MagicMock
import openai
from pydantic import ValidationError

from app.services.classifier import classify_ticket_text, ClassificationOutcome, FALLBACK_CLASSIFICATION
from app.models.ticket import TicketType, TicketPriority
from app.schemas.classification import AreaCode, TicketClassification

@pytest.mark.unit
def test_classify_happy_path(mocker):
    mock_client = mocker.patch("app.services.classifier.client")
    mock_message = MagicMock()
    mock_message.message.parsed = TicketClassification(
        ticket_type=TicketType.PETITION,
        priority=TicketPriority.MEDIUM,
        responsible_area=AreaCode.ATENCION_USUARIO,
        decision_justification="Test justification valid length"
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_message]
    mock_response.model_dump.return_value = {"mock": "data"}
    mock_response.usage.total_tokens = 50
    mock_client.beta.chat.completions.parse.return_value = mock_response

    mocker.patch("time.perf_counter", side_effect=[0.0, 0.1])

    outcome = classify_ticket_text("Test text")
    assert isinstance(outcome, ClassificationOutcome)
    assert outcome.classification.decision_justification == "Test justification valid length"
    assert outcome.tokens_used == 50
    assert outcome.raw_response == {"mock": "data"}
    assert outcome.latency_ms == 100

@pytest.mark.unit
def test_classify_fallback_on_api_error(mocker):
    mock_client = mocker.patch("app.services.classifier.client")
    mock_client.beta.chat.completions.parse.side_effect = openai.APIError(
        message="API down", request=MagicMock(), body=None
    )

    mocker.patch("time.sleep")
    
    outcome = classify_ticket_text("Test text")
    assert outcome.classification == FALLBACK_CLASSIFICATION
    assert mock_client.beta.chat.completions.parse.call_count == 3
    assert outcome.raw_response is None
    assert outcome.tokens_used is None

@pytest.mark.unit
def test_classifier_fallback_outcome_has_no_metadata(mocker):
    mock_client = mocker.patch("app.services.classifier.client")
    mock_client.beta.chat.completions.parse.side_effect = Exception("General error")
    mocker.patch("time.sleep")
    
    outcome = classify_ticket_text("Test text")
    assert outcome.classification == FALLBACK_CLASSIFICATION
    assert outcome.raw_response is None
    assert outcome.tokens_used is None
    assert outcome.latency_ms is None

@pytest.mark.unit
def test_classifier_retries_on_validation_error(mocker):
    mock_client = mocker.patch("app.services.classifier.client")
    
    mock_message = MagicMock()
    mock_message.message.parsed = None
    mock_response = MagicMock()
    mock_response.choices = [mock_message]
    mock_client.beta.chat.completions.parse.return_value = mock_response

    mocker.patch("time.sleep")
    
    outcome = classify_ticket_text("Test text")
    assert outcome.classification == FALLBACK_CLASSIFICATION
    assert mock_client.beta.chat.completions.parse.call_count == 3

@pytest.mark.unit
def test_classifier_system_prompt(mocker):
    mock_client = mocker.patch("app.services.classifier.client")
    mock_message = MagicMock()
    mock_message.message.parsed = TicketClassification(
        ticket_type=TicketType.PETITION,
        priority=TicketPriority.MEDIUM,
        responsible_area=AreaCode.ATENCION_USUARIO,
        decision_justification="Test justification valid length"
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_message]
    mock_client.beta.chat.completions.parse.return_value = mock_response

    classify_ticket_text("Test text")
    
    call_kwargs = mock_client.beta.chat.completions.parse.call_args.kwargs
    messages = call_kwargs["messages"]
    system_prompt = next(m["content"] for m in messages if m["role"] == "system")
    assert "Law 1755" in system_prompt
