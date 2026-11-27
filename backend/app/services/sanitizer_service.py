import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

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


_PRESIDIO_AVAILABLE = False
_analyzer = None
_anonymizer = None

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

    _nlp_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "es", "model_name": "es_core_news_md"}],
    }
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
            score_threshold=0.5,
        )
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
