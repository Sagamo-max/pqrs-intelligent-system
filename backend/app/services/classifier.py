from openai import OpenAI
from app.core.config import settings
from app.schemas.classification import PQRSClassification


client = OpenAI(api_key=settings.AI_API_KEY)

def classify_pqrs_text(text: str) -> PQRSClassification:
    """
    Envía el texto sanitizado al LLM para clasificarlo obligatoriamente
    bajo el esquema PQRSClassification.
    """
    system_prompt = (
        "Eres un agente experto en triaje corporativo y legislación colombiana (Ley 1755). "
        "Tu única tarea es analizar el texto del usuario y clasificar la solicitud "
        "estrictamente en el formato JSON solicitado. Sé objetivo y analítico."
    )

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        response_format=PQRSClassification,
        temperature=0.1 
    )

    return response.choices[0].message.parsed