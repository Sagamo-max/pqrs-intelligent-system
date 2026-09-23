from openai import OpenAI
from app.core.config import settings
from app.schemas.classification import TicketClassification


client = OpenAI(api_key=settings.AI_API_KEY)

def classify_ticket_text(text: str) -> TicketClassification:
    """
    Sends sanitized text to the LLM for classification using the
    TicketClassification schema.
    """
    system_prompt = (
        "You are an expert agent in corporate triage and Colombian legislation (Law 1755). "
        "Your only task is to analyze the user text and classify the request "
        "strictly in the requested JSON format. Be objective and analytical. "
        "Use the exact Spanish enum values defined by the response schema."
    )

    response = client.beta.chat.completions.parse(
        model=settings.AI_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        response_format=TicketClassification,
    )

    return response.choices[0].message.parsed