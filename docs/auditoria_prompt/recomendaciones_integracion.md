# Recomendaciones de Integración en el Backend SmartPQRS

> **Restricción respetada:** Esta guía detalla cómo integrar `prompt_mejorado_v2.txt`, la validación estricta de salida y el registro de `posible_inyeccion` **reutilizando exactamente las tablas, columnas y endpoints actuales** del repositorio, sin requerir migraciones de base de datos ni cambios de contratos HTTP.

---

## 1. Pre-sanitización de delimitadores antes de invocar al LLM

En `backend/app/services/ticket_service.py`, el texto pasa primero por `sanitize_text(free_text)` (Presidio). Antes de interpolar `{{TEXTO_PQRS}}` en `USER_DATA_TEMPLATE`:

1. **Neutralizar delimitadores reservados:** eliminar o reemplazar cualquier aparición literal de `<<<SMRT_PQRS_8F4D_INI>>>` y `<<<SMRT_PQRS_8F4D_FIN>>>` en el texto sanitizado para impedir ataques de *delimiter spoofing* (Vector V-03).
2. **Proteger el prefijo de allowlist `[QA-SEC-TEST]`:** si la solicitud no fue originada en una prueba interna autenticada por rol `MASTER`, remover cualquier aparición literal de `[QA-SEC-TEST]` del texto ciudadano antes de enviarlo al modelo.

```python
DELIM_START = "<<<SMRT_PQRS_8F4D_INI>>>"
DELIM_END = "<<<SMRT_PQRS_8F4D_FIN>>>"

def build_user_message(sanitized_text: str, allow_qa_tag: bool = False) -> str:
    safe_text = (
        sanitized_text
        .replace(DELIM_START, "[DELIM_REMOVED]")
        .replace(DELIM_END, "[DELIM_REMOVED]")
    )
    if not allow_qa_tag:
        safe_text = safe_text.replace("[QA-SEC-TEST]", "")

    return (
        "USER_DATA_TO_PROCESS:\n"
        f"{DELIM_START}\n{safe_text}\n{DELIM_END}"
    )
```

---

## 2. Validación estricta de salida (JSON Schema + Pydantic v2)

Para garantizar compatibilidad con **GPT-4o, Claude y Gemini** sin depender de `fine-tuning`:

1. Definir un esquema Pydantic cerrado (`extra="forbid"`) para parsear la respuesta del LLM y mapearla de forma determinista hacia los enums internos ya existentes (`TicketType`, `TicketPriority`, `AreaCode`):

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.ticket import TicketPriority, TicketType
from app.schemas.classification import AreaCode

CATEGORY_TO_TICKET_TYPE = {
    "PETICIÓN": TicketType.PETITION,
    "QUEJA": TicketType.COMPLAINT,
    "RECLAMO": TicketType.CLAIM,
    "SUGERENCIA": TicketType.SUGGESTION,
}

PRIORITY_TO_ENUM = {
    "ALTA": TicketPriority.HIGH,
    "MEDIA": TicketPriority.MEDIUM,
    "BAJA": TicketPriority.LOW,
}

class PromptV2Output(BaseModel):
    model_config = ConfigDict(extra="forbid")

    justificacion: str = Field(..., min_length=10, max_length=220)
    categoria: Literal["PETICIÓN", "QUEJA", "RECLAMO", "SUGERENCIA"]
    prioridad: Literal["ALTA", "MEDIA", "BAJA"]
    dependencia: AreaCode
    confianza: float = Field(..., ge=0.0, le=1.0)
    es_ambiguo: bool
    posible_inyeccion: bool

    @field_validator("justificacion")
    @classmethod
    def validate_max_words(cls, v: str) -> str:
        clean = " ".join(v.strip().split())
        if len(clean.split()) > 25:  # margen técnico sobre instrucción de 20 palabras
            raise ValueError("justificacion excede el límite permitido de palabras")
        return clean
```

2. **Configuración por proveedor sin cambiar la lógica de negocio:**
   - **OpenAI (GPT-4o / GPT-4o-mini):** `response_format=PromptV2Output` (Structured Outputs con `strict: true`) + `temperature=0`.
   - **Google Gemini:** `config={"response_mime_type": "application/json", "response_schema": PromptV2Output, "temperature": 0.0}`.
   - **Anthropic Claude:** forzar herramienta única (`tool_choice={"type": "tool", "name": "emit_classification"}`) con `PromptV2Output.model_json_schema()`, o validar el texto devuelto con `PromptV2Output.model_validate_json(raw_text)`.
   - Si la validación JSON falla, se activa exactamente la misma cascada resiliente ya existente en `classifier.py` (reintento → `heuristic_classify` → `FALLBACK_CLASSIFICATION`).

---

## 3. Persistencia y Logging de `posible_inyeccion`, `confianza` y `es_ambiguo` (sin tocar el esquema SQL)

El modelo actual de base de datos (`ai_audits` y `tickets`) **ya posee las columnas necesarias** para almacenar toda la telemetría del Prompt v2 sin migraciones adicionales:

| Campo del Prompt v2 | Destino en BD actual (`ai_audits` / `tickets`) | Acción recomendada en el servicio |
|---|---|---|
| `confianza` | `ai_audits.confidence` (`Float`, actualmente guardado como `None`) | Poblar `ClassificationOutcome.confidence = parsed.confianza` para aprovechar la columna existente. |
| `justificacion` | `ai_audits.decision_justification` (`Text`) | Guardar directamente; se expone en `GET /api/pqrs/{id}` (HU-16) y `GET /api/pqrs/{id}/auditoria-ia` (HU-17). |
| `posible_inyeccion` | `ai_audits.raw_response` (`JSONB`) + logs de seguridad | Incluir el JSON validado dentro de `raw_response["parsed_v2"]` y emitir alerta estructurada en el logger. |
| `es_ambiguo` | `ai_audits.raw_response` (`JSONB`) + `tickets.needs_sla_validation` (opcional) | Conservar en `raw_response["parsed_v2"]` para analítica de incertidumbre y revisión supervisada. |

### Alerta estructurada cuando `posible_inyeccion == True`

En `audit_service.py` o `ticket_service.py`, agregar un evento de log auditable sin interrumpir la radicación legal de la PQRS (cumpliendo la Ley 1755 de 2015, que impide rechazar de plano una radicación sin revisión):

```python
if parsed_v2.posible_inyeccion:
    logger.warning(
        "SECURITY_PROMPT_INJECTION_DETECTED ticket_id=%s tracking=%s model=%s categoria=%s confianza=%.2f",
        ticket.id,
        ticket.tracking_number,
        settings.AI_MODEL_NAME,
        parsed_v2.categoria,
        parsed_v2.confianza,
    )
```

### Enrutamiento preventivo a revisión humana

Sin modificar tablas ni endpoints:
- Cuando `parsed_v2.posible_inyeccion is True` o `parsed_v2.confianza < 0.70`, el servicio puede marcar `ticket.needs_sla_validation = True` (bandera booleana **ya existente** en `tickets` y filtrable mediante `GET /api/v1/pqrs/?needs_sla_validation=true`), haciendo que los casos ambiguos o sospechosos de manipulación aparezcan automáticamente en la bandeja de revisión de supervisores.

---

## 4. Optimización de costos en producción (Prompt Caching)

- `SYSTEM_INSTRUCTIONS` en `prompt_mejorado_v2.txt` es **100% estático** entre solicitudes (todas las variables ciudadanas viajan aisladas en `USER_DATA_TEMPLATE`).
- En proveedores con **Prompt Caching** (OpenAI, Anthropic `cache_control: {"type": "ephemeral"}`, Google Gemini Context Caching), mantener `SYSTEM_INSTRUCTIONS` inmutable en el mensaje `system` permite cachear los tokens fijos de reglas y few-shot con descuentos del **50% al 90%** en tokens de entrada y menor latencia TTFT (*Time To First Token*).
- Si se despliega sobre un proveedor local o sin caché de prefijo con restricción severa de ventana, puede omitirse únicamente la sección `[EJEMPLOS DE REFERENCIA]` conservando intactas las secciones normativas, de seguridad y de reglas híbridas (modo *v2 Compacto Zero-Shot*, documentado en `estimacion_tokens.md`).
