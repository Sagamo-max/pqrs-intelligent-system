import logging
import re
import unicodedata
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Capa B: Umbral más estricto para NER PERSON (SpacyRecognizer asigna 0.85 por defecto;
# las entidades regex PII conservan score_threshold=0.5).
PERSON_SCORE_THRESHOLD = 0.85
REGEX_SCORE_THRESHOLD = 0.5

# Capa C: Ignorar entidad MISC de spaCy (ruido no-PII y warning en Presidio)
_NER_LABELS_TO_IGNORE = ["MISC"]

_CEDULA_REGEX = r"\b\d{1,3}(?:[.,\s]\d{3}){2,3}\b|\b\d(?:\s\d){5,9}\b|\b\d{6,10}\b"
_PHONE_REGEX = r"(?<!\w)(?:\+?57[\s.\-]?)?(?:3\d{2}|60[1-8])[\s.\-]?\d{3}[\s.\-]?\d{4}\b"
_NIT_REGEX = r"\b\d{3}[.,\s]?\d{3}[.,\s]?\d{3}-\d\b|\b[89]\d{2}[.,\s]?\d{3}[.,\s]?\d{3}[\-\s]?\d\b"
_ADDRESS_REGEX = (
    r"(?i)\b(?:calle|carrera|cra\.?|cll\.?|avenida|av\.?|transversal|diagonal)"
    r"\s+\d+[a-zA-Z]?\s*(?:#|no\.?|nro\.?)\s*\d+\s*-\s*\d+\b"
)
_EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

_MASK_VALUES = {
    "EMAIL_ADDRESS": "[MASKED_EMAIL]",
    "PHONE_NUMBER": "[MASKED_PHONE]",
    "PERSON": "[MASKED_NAME]",
    "CO_CEDULA": "[MASKED_DOCUMENT]",
    "CO_NIT": "[MASKED_NIT]",
    "CO_ADDRESS": "[MASKED_ADDRESS]",
}

# Capa A: Allowlist post-NER de palabras/frases comunes en PQRS (normalizadas sin tildes)
ALLOWLIST_TOKENS: frozenset[str] = frozenset(
    {
        # Verbos de cortesía y primera persona habituales en PQRS
        "agradezco",
        "agradecemos",
        "solicito",
        "solicitamos",
        "manifiesto",
        "manifestamos",
        "expreso",
        "expresamos",
        "presento",
        "presentamos",
        "requiero",
        "requerimos",
        "pido",
        "pedimos",
        "pueden",
        "puede",
        "escribo",
        "escribimos",
        "acudo",
        "acudimos",
        "elevo",
        "dejo",
        "dejamos",
        "sugiero",
        "sugerimos",
        "propongo",
        "proponemos",
        "recomiendo",
        "recomendamos",
        "exijo",
        "exigimos",
        "reclamo",
        "reclamamos",
        "quiero",
        "queremos",
        "necesito",
        "necesitamos",
        "espero",
        "esperamos",
        "informo",
        "informamos",
        "adjunto",
        "comunico",
        "dirijo",
        "confirmo",
        "confirmamos",
        "reitero",
        "observo",
        "observamos",
        "notamos",
        "adquirimos",
        "suscribimos",
        "llevamos",
        "seguimos",
        "actuando",
        "deseo",
        "aclaro",
        "brindar",
        "habia",
        "habiamos",
        "quisiera",
        "considero",
        "consulto",
        "radico",
        "radicamos",
        "reporto",
        "verifique",
        "verificamos",
        # Fórmulas de saludo, cierre, conectores, adverbios y pronombres
        "atentamente",
        "cordialmente",
        "respetuosamente",
        "cordial",
        "saludo",
        "buenos",
        "buenas",
        "buen",
        "hola",
        "estimados",
        "senor",
        "senora",
        "senores",
        "senoras",
        "doctor",
        "doctora",
        "gracias",
        "por",
        "lo",
        "anterior",
        "sin",
        "embargo",
        "ademas",
        "asimismo",
        "finalmente",
        "igualmente",
        "actualmente",
        "previamente",
        "pese",
        "aunque",
        "ante",
        "dada",
        "dado",
        "desde",
        "durante",
        "mediante",
        "conforme",
        "respecto",
        "justo",
        "nuestro",
        "nuestra",
        "ojala",
        "le",
        "les",
        "me",
        "nos",
        "vea",
        "oiga",
        "mire",
        "pero",
        "entonces",
        "que",
        # Meses y días de la semana
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
        # Cargos genéricos, tratamientos, áreas SmartPQRS, siglas y placeholders
        "funcionario",
        "funcionaria",
        "asesor",
        "asesora",
        "coordinador",
        "coordinadora",
        "supervisor",
        "supervisora",
        "director",
        "directora",
        "analista",
        "operador",
        "operadora",
        "vigilante",
        "repartidor",
        "mensajero",
        "tecnico",
        "abogado",
        "ciudadano",
        "ciudadana",
        "usuario",
        "usuaria",
        "cliente",
        "representante",
        "gerente",
        "presidente",
        "paciente",
        "trabajador",
        "familiar",
        "vecino",
        "vecina",
        "sumerce",
        "parcero",
        "talento",
        "humano",
        "talento humano",
        "atencion",
        "atencion al usuario",
        "facturacion",
        "cartera",
        "ventas",
        "soporte",
        "soporte tecnico",
        "ti",
        "logistica",
        "administracion",
        "juridica",
        "pqrs",
        "pqrsd",
        "dian",
        "secop",
        "nit",
        "cc",
        "c.c.",
        "xxx",
        "c.c. xxx",
        "xml",
        "pdf",
        "ipc",
    }
)

_FALLBACK_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("EMAIL_ADDRESS", re.compile(_EMAIL_REGEX), _MASK_VALUES["EMAIL_ADDRESS"]),
    ("PHONE_NUMBER", re.compile(_PHONE_REGEX), _MASK_VALUES["PHONE_NUMBER"]),
    ("CO_NIT", re.compile(_NIT_REGEX), _MASK_VALUES["CO_NIT"]),
    ("CO_ADDRESS", re.compile(_ADDRESS_REGEX), _MASK_VALUES["CO_ADDRESS"]),
    ("CO_CEDULA", re.compile(_CEDULA_REGEX), _MASK_VALUES["CO_CEDULA"]),
]


@dataclass(frozen=True)
class _FallbackOperatorConfig:
    operator_name: str
    params: dict[str, str]


def _normalize_token(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    stripped_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped_accents.casefold().strip().split())


def _is_sentence_initial(text: str, start: int) -> bool:
    if start <= 0:
        return True
    prefix = text[:start].rstrip(" \t\r")
    if not prefix:
        return True
    return prefix[-1] in {".", "!", "?", "\n", ":"}


def _should_keep_ner_person(text: str, start: int, end: int, score: float) -> bool:
    if score < PERSON_SCORE_THRESHOLD:
        return False

    span = text[start:end]
    normalized_span = _normalize_token(span)
    if not normalized_span:
        return False

    if normalized_span in ALLOWLIST_TOKENS:
        return False

    word_tokens = re.findall(r"[^\W\d_]+(?:\.[^\W\d_]+)*\.?", normalized_span)
    if word_tokens and all(
        tok in ALLOWLIST_TOKENS or tok.rstrip(".") in ALLOWLIST_TOKENS
        for tok in word_tokens
    ):
        return False

    # Filtro posicional: evitar falsos positivos en 1 sola palabra capitalizada por inicio de oración
    if len(word_tokens) == 1 and _is_sentence_initial(text, start):
        return False

    return True


def _filter_analyzer_results(text: str, results: list) -> list:
    filtered = []
    for res in results:
        if res.entity_type == "PERSON":
            if _should_keep_ner_person(text, res.start, res.end, float(res.score)):
                filtered.append(res)
        else:
            filtered.append(res)
    return filtered


_PRESIDIO_AVAILABLE = False
_analyzer = None
_anonymizer = None
_nlp_engine = None
_nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "es", "model_name": "es_core_news_md"}],
    "ner_model_configuration": {
        "labels_to_ignore": list(_NER_LABELS_TO_IGNORE),
    },
}

try:
    from presidio_analyzer import (
        AnalyzerEngine,
        Pattern,
        PatternRecognizer,
        RecognizerRegistry,
    )
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    _provider = NlpEngineProvider(nlp_configuration=_nlp_config)
    _nlp_engine = _provider.create_engine()

    _cedula_recognizer = PatternRecognizer(
        supported_entity="CO_CEDULA",
        patterns=[Pattern(name="co_cedula_pattern", regex=_CEDULA_REGEX, score=0.85)],
        supported_language="es",
        context=[
            "cédula",
            "cedula",
            "CC",
            "C.C.",
            "documento",
            "identificación",
            "identificacion",
            "NUIP",
            "DNI",
        ],
    )
    _phone_recognizer = PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=[Pattern(name="co_phone_pattern", regex=_PHONE_REGEX, score=0.85)],
        supported_language="es",
        context=[
            "teléfono",
            "telefono",
            "celular",
            "contacto",
            "móvil",
            "movil",
            "llamar",
            "número",
            "numero",
        ],
    )
    _nit_recognizer = PatternRecognizer(
        supported_entity="CO_NIT",
        patterns=[Pattern(name="co_nit_pattern", regex=_NIT_REGEX, score=0.85)],
        supported_language="es",
        context=["NIT", "nit", "identificación tributaria", "rut"],
    )
    _address_recognizer = PatternRecognizer(
        supported_entity="CO_ADDRESS",
        patterns=[Pattern(name="co_address_pattern", regex=_ADDRESS_REGEX, score=0.85)],
        supported_language="es",
        context=["dirección", "direccion", "domicilio", "residencia", "ubicado", "sede"],
    )

    _registry = RecognizerRegistry(supported_languages=["es"])
    _registry.load_predefined_recognizers(languages=["es"])
    _registry.add_recognizer(_cedula_recognizer)
    _registry.add_recognizer(_phone_recognizer)
    _registry.add_recognizer(_nit_recognizer)
    _registry.add_recognizer(_address_recognizer)

    _analyzer = AnalyzerEngine(
        nlp_engine=_nlp_engine,
        registry=_registry,
        supported_languages=["es"],
    )
    _anonymizer = AnonymizerEngine()
    _OPERATORS = {
        entity: OperatorConfig("replace", {"new_value": mask})
        for entity, mask in _MASK_VALUES.items()
    }
    _PRESIDIO_AVAILABLE = True
except Exception as exc:  # pragma: no cover - fallback when spaCy/Presidio unavailable
    logger.warning(
        "Presidio/spaCy unavailable (%s); using deterministic regex fallback.",
        exc,
    )
    _OPERATORS = {
        entity: _FallbackOperatorConfig("replace", {"new_value": mask})
        for entity, mask in _MASK_VALUES.items()
    }


def _regex_fallback_anonymize(text: str, entities: list[str]) -> str:
    allowed = set(entities)
    result = text
    for entity, pattern, replacement in _FALLBACK_RULES:
        if entity in allowed:
            result = pattern.sub(replacement, result)
    return result


def _anonymize(text: str, entities: list[str]) -> str:
    if _analyzer is not None and _anonymizer is not None:
        results = _analyzer.analyze(
            text=text,
            language="es",
            entities=entities,
            score_threshold=REGEX_SCORE_THRESHOLD,
        )
        results = _filter_analyzer_results(text, results)
        if not results:
            return text

        return _anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=_OPERATORS,
        ).text

    return _regex_fallback_anonymize(text, entities)


def mask_regex_patterns(text: str) -> str:
    if not text:
        return text
    return _anonymize(
        text,
        ["EMAIL_ADDRESS", "PHONE_NUMBER", "CO_CEDULA", "CO_NIT", "CO_ADDRESS"],
    )


def mask_ner_patterns(text: str) -> str:
    if not text:
        return text
    return _anonymize(text, ["PERSON"])


def sanitize_text(text: str | None) -> str | None:
    if not text:
        return text

    try:
        return _anonymize(
            text,
            ["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "CO_CEDULA", "CO_NIT", "CO_ADDRESS"],
        )
    except Exception:
        logger.exception("Presidio sanitization failed; returning original text")
        return text
