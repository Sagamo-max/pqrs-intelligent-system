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
    name="cedula_co_pattern",
    regex=r"\b\d{1,2}[.,]?\d{3}[.,]?\d{3}\b|\b1\d{9}\b",
    score=0.8,
)
_cedula_recognizer = PatternRecognizer(
    supported_entity="CO_CEDULA",
    patterns=[_cedula_pattern],
    supported_language="es",
    context=["cédula", "cedula", "documento", "identificación", "NUIP"],
)
_phone_recognizer = PatternRecognizer(
    supported_entity="CO_PHONE",
    patterns=[
        Pattern(
            name="colombian_phone_pattern",
            regex=r"\b3\d{9}\b",
            score=0.8,
        )
    ],
    supported_language="es",
    context=["teléfono", "telefono", "celular", "móvil", "movil", "llamar"],
)

_registry = RecognizerRegistry(supported_languages=["es"])
_registry.load_predefined_recognizers(languages=["es"])
_registry.add_recognizer(_cedula_recognizer)
_registry.add_recognizer(_phone_recognizer)

_analyzer = AnalyzerEngine(
    nlp_engine=_nlp_engine,
    registry=_registry,
    supported_languages=["es"],
)
_anonymizer = AnonymizerEngine()

_OPERATORS = {
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[MASKED_EMAIL]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[MASKED_PHONE]"}),
    "CO_PHONE": OperatorConfig("replace", {"new_value": "[MASKED_PHONE]"}),
    "PERSON": OperatorConfig("replace", {"new_value": "[MASKED_NAME]"}),
    "CO_CEDULA": OperatorConfig("replace", {"new_value": "[MASKED_DOCUMENT]"}),
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
        ["EMAIL_ADDRESS", "PHONE_NUMBER", "CO_PHONE", "CO_CEDULA"],
    )


def mask_ner_patterns(text: str) -> str:
    return _anonymize(text, ["PERSON"])


def sanitize_text(text: str) -> str:
    if not text:
        return text

    try:
        return _anonymize(
            text,
            ["EMAIL_ADDRESS", "PHONE_NUMBER", "CO_PHONE", "PERSON", "CO_CEDULA"],
        )
    except Exception:
        logger.exception("Presidio sanitization failed; returning original text")
        return text
