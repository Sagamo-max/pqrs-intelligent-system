import logging

from openai import OpenAI
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_openai(text: str) -> TicketClassification:
    system_prompt = (
        "You are an expert agent in corporate triage and Colombian legislation (Law 1755). "
        "Your only task is to analyze the user text and classify the request "
        "strictly in the requested JSON format. Be objective and analytical. "
        "Use the exact enum values defined by the response schema; do not invent new ones."
    )

    response = client.beta.chat.completions.parse(
        model=settings.AI_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        response_format=TicketClassification,
    )
    return response.choices[0].message.parsed


def classify_ticket_text(text: str) -> TicketClassification:
    try:
        return _call_openai(text)
    except Exception:
        logger.exception("AI classification failed; falling back to defaults.")
        return FALLBACK_CLASSIFICATION