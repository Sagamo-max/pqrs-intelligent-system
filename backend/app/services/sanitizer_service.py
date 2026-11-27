import logging

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

_nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "es", "model_name": "es_core_news_md"}],
}
_provider = NlpEngineProvider(nlp_configuration=_nlp_config)
_nlp_engine = _provider.create_engine()

_cedula_pattern = Pattern(
    name="co_cedula_pattern",
    regex=r"\b\d{1,3}(?:[.,]\d{3}){1,3}\b|\b\d{6,10}\b",
    score=0.85,
)
_cedula_recognizer = PatternRecognizer(
    supported_entity="CO_CEDULA",
    patterns=[_cedula_pattern],
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
_phone_pattern = Pattern(
    name="co_phone_pattern",
    regex=r"\b(?:\+?57[\s\-]?)?3\d{2}[\s\-]?\d{3}[\s\-]?\d{4}\b",
    score=0.85,
)
_phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER",
    patterns=[_phone_pattern],
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
_nit_pattern = Pattern(
    name="co_nit_pattern",
    regex=r"\b\d{3}[.,]?\d{3}[.,]?\d{3}[\-]?\d\b",
    score=0.85,
)
_nit_recognizer = PatternRecognizer(
    supported_entity="CO_NIT",
    patterns=[_nit_pattern],
    supported_language="es",
    context=["NIT", "nit", "identificación tributaria", "rut"],
)

_registry = RecognizerRegistry(supported_languages=["es"])
_registry.load_predefined_recognizers(languages=["es"])
_registry.add_recognizer(_cedula_recognizer)
_registry.add_recognizer(_phone_recognizer)
_registry.add_recognizer(_nit_recognizer)

_analyzer = AnalyzerEngine(
    nlp_engine=_nlp_engine,
    registry=_registry,
    supported_languages=["es"],
)
_anonymizer = AnonymizerEngine()

_OPERATORS = {
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[MASKED_EMAIL]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[MASKED_PHONE]"}),
    "PERSON": OperatorConfig("replace", {"new_value": "[MASKED_NAME]"}),
    "CO_CEDULA": OperatorConfig("replace", {"new_value": "[MASKED_DOCUMENT]"}),
    "CO_NIT": OperatorConfig("replace", {"new_value": "[MASKED_NIT]"}),
}


def _anonymize(text: str, entities: list[str]) -> str:
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


def mask_regex_patterns(text: str) -> str:
    return _anonymize(
        text,
        ["EMAIL_ADDRESS", "PHONE_NUMBER", "CO_CEDULA", "CO_NIT"],
    )


def mask_ner_patterns(text: str) -> str:
    return _anonymize(text, ["PERSON"])


def sanitize_text(text: str) -> str:
    if not text:
        return text

    try:
        return _anonymize(
            text,
            ["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "CO_CEDULA", "CO_NIT"],
        )
    except Exception:
        logger.exception("Presidio sanitization failed; returning original text")
        return text
