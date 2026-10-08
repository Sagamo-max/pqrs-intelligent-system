import logging
import time
from dataclasses import dataclass

from openai import OpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.ticket import TicketPriority, TicketType
from app.schemas.classification import AreaCode, TicketClassification

logger = logging.getLogger(__name__)

client_options = {"api_key": settings.OPENAI_API_KEY}
if settings.AI_BASE_URL:
    client_options["base_url"] = settings.AI_BASE_URL

client = OpenAI(**client_options)


FALLBACK_CLASSIFICATION = TicketClassification(
    ticket_type=TicketType.PETITION,
    priority=TicketPriority.MEDIUM,
    responsible_area=AreaCode.ATENCION_USUARIO,
    decision_justification=(
        "Automatic classification unavailable; request routed to customer service."
    ),
)


@dataclass
class ClassificationOutcome:
    classification: TicketClassification
    raw_response: dict | None = None
    tokens_used: int | None = None
    latency_ms: int | None = None
    confidence: float | None = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_openai(text: str) -> ClassificationOutcome:
    system_prompt = (
        "You are an expert agent in corporate triage and Colombian legislation (Law 1755). "
        "Your only task is to analyze the user text and classify the request "
        "strictly in the requested JSON format. Be objective and analytical. "
        "Use the exact enum values defined by the response schema; do not invent new ones. "
        "The decision_justification field is mandatory and must be a non-empty explanation."
    )

    start = time.perf_counter()
    response = client.beta.chat.completions.parse(
        model=settings.AI_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        response_format=TicketClassification,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    parsed = response.choices[0].message.parsed

    # Forzar validación explícita para disparar retry si el LLM devolvió
    # una justificación vacía aunque Pydantic no lo haya atrapado en parse().
    if parsed is None:
        raise ValidationError.from_exception_data(
            "TicketClassification",
            [{"type": "value_error", "loc": ("decision_justification",), "input": None, "ctx": {"error": "Missing classification"}}],
        )

    outcome = ClassificationOutcome(
        classification=parsed,
        raw_response=response.model_dump(mode="json"),
        tokens_used=getattr(response.usage, "total_tokens", None) if response.usage else None,
        latency_ms=latency_ms,
        confidence=None,  # OpenAI Structured Outputs no expone probabilidad por campo
    )
    return outcome


def classify_ticket_text(text: str) -> ClassificationOutcome:
    try:
        return _call_openai(text)
    except Exception:
        logger.exception("AI classification failed; falling back to defaults.")
        return ClassificationOutcome(
            classification=FALLBACK_CLASSIFICATION,
            raw_response=None,
            tokens_used=None,
            latency_ms=None,
            confidence=None,
        )