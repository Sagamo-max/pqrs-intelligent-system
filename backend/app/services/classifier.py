import logging
import time
from dataclasses import dataclass, field

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.models.ticket import TicketPriority, TicketType
from app.schemas.classification import AreaCode, TicketClassification
from app.services.heuristic_classifier import heuristic_classify

logger = logging.getLogger(__name__)

client_options = {"api_key": settings.OPENAI_API_KEY}
if settings.AI_BASE_URL:
    client_options["base_url"] = settings.AI_BASE_URL

client = OpenAI(**client_options)


RETRYABLE_EXCEPTIONS = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)

NON_RETRYABLE_EXCEPTIONS = (
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    BadRequestError,
)


FALLBACK_CLASSIFICATION = TicketClassification(
    ticket_type=TicketType.PETITION,
    priority=TicketPriority.MEDIUM,
    responsible_area=AreaCode.ATENCION_USUARIO,
    decision_justification=(
        "Automatic classification unavailable; request routed to customer service."
    ),
)


@dataclass
class AttemptInfo:
    attempt_number: int
    error_type: str
    error_message: str
    latency_ms: int


@dataclass
class ClassificationOutcome:
    classification: TicketClassification
    source: str  # "openai" | "heuristic" | "fallback"
    raw_response: dict | None = None
    tokens_used: int | None = None
    latency_ms: int | None = None
    confidence: float | None = None
    attempts: list[AttemptInfo] = field(default_factory=list)


def _call_openai_once(text: str) -> ClassificationOutcome:
    system_prompt = (
        "You are an expert agent in corporate triage and Colombian legislation (Law 1755). "
        "Your only task is to analyze the user text and classify the request "
        "strictly in the requested JSON format. Be objective and analytical. "
        "Use the exact enum values defined by the response schema; do not invent new ones. "
        "The decision_justification field is mandatory, must be a non-empty explanation, "
        "and MUST be written in Spanish (the auditor is a Spanish speaker)."
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
    if parsed is None:
        raise RuntimeError("OpenAI returned an empty classification")

    return ClassificationOutcome(
        classification=parsed,
        source="openai",
        raw_response=response.model_dump(mode="json"),
        tokens_used=getattr(response.usage, "total_tokens", None) if response.usage else None,
        latency_ms=latency_ms,
        confidence=None,
        attempts=[],
    )


@retry(
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_openai_with_retry(text: str) -> ClassificationOutcome:
    return _call_openai_once(text)


def _try_openai(text: str, attempts: list[AttemptInfo]) -> ClassificationOutcome | None:
    try:
        return _call_openai_with_retry(text)
    except Exception as exc:
        is_retryable = isinstance(exc, RETRYABLE_EXCEPTIONS)
        attempts_count = 3 if is_retryable else 1

        for i in range(1, attempts_count + 1):
            attempts.append(
                AttemptInfo(
                    attempt_number=i,
                    error_type=type(exc).__name__,
                    error_message=str(exc)[:500],
                    latency_ms=0,
                )
            )

        logger.warning(
            "OpenAI classification failed after %d attempt(s): %s",
            attempts_count,
            type(exc).__name__,
        )
        return None


def _try_heuristic(text: str) -> ClassificationOutcome | None:
    area = heuristic_classify(text)
    if area is None:
        return None

    return ClassificationOutcome(
        classification=TicketClassification(
            ticket_type=TicketType.PETITION,
            priority=TicketPriority.MEDIUM,
            responsible_area=area,
            decision_justification=(
                "Clasificación automática no disponible; "
                "asignada por heurística local de palabras clave."
            ),
        ),
        source="heuristic",
        raw_response=None,
        tokens_used=None,
        latency_ms=None,
        confidence=None,
        attempts=[],
    )


def _build_fallback() -> ClassificationOutcome:
    return ClassificationOutcome(
        classification=FALLBACK_CLASSIFICATION,
        source="fallback",
        raw_response=None,
        tokens_used=None,
        latency_ms=None,
        confidence=None,
        attempts=[],
    )


def classify_ticket_text(text: str) -> ClassificationOutcome:
    """
    Cascade of classification strategies:
        1. OpenAI (with smart retry)
        2. Local keyword heuristic
        3. Fixed fallback (ATENCION_USUARIO / PETITION / MEDIUM)

    Never raises. Never blocks the ticket.
    """
    attempts: list[AttemptInfo] = []

    outcome = _try_openai(text, attempts)
    if outcome is not None:
        outcome.attempts = attempts
        return outcome

    outcome = _try_heuristic(text)
    if outcome is not None:
        outcome.attempts = attempts
        logger.info(
            "Classified via heuristic fallback (area=%s)",
            outcome.classification.responsible_area,
        )
        return outcome

    outcome = _build_fallback()
    outcome.attempts = attempts
    logger.warning("Classified via fixed fallback (ATENCION_USUARIO)")
    return outcome