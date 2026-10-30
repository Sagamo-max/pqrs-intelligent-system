import pytest
from app.services.sanitizer_service import sanitize_text, mask_regex_patterns, mask_ner_patterns

@pytest.mark.unit
def test_mask_emails():
    text = "Mi correo es test@example.com y otro@test.co."
    masked = mask_regex_patterns(text)
    assert "[MASKED_EMAIL]" in masked
    assert "test@example.com" not in masked

@pytest.mark.unit
def test_mask_phones():
    text = "Llamar al 3001234567 o al 3159876543."
    masked = mask_regex_patterns(text)
    assert masked.count("[MASKED_PHONE]") == 2
    assert "3001234567" not in masked

@pytest.mark.unit
def test_mask_documents():
    texts = [
        ("cédula 12345678", "cédula [MASKED_DOCUMENT]"),
        ("CC 98765432", "CC [MASKED_DOCUMENT]"),
        ("documento 5555555", "documento [MASKED_DOCUMENT]")
    ]
    for original, expected in texts:
        assert mask_regex_patterns(original) == expected

@pytest.mark.unit
def test_mask_names():
    text = "Juan Pérez estuvo aquí."
    masked = mask_ner_patterns(text)
    assert "[MASKED_NAME]" in masked
    assert "Juan Pérez" not in masked

@pytest.mark.unit
def test_sanitize_no_pii():
    text = "Este es un texto sin datos personales que pueda causar problemas."
    assert sanitize_text(text) == text

@pytest.mark.unit
def test_sanitize_returns_string_not_tuple():
    text = "Mi nombre es Juan Pérez y mi cédula 12345678"
    result = sanitize_text(text)
    assert isinstance(result, str)
    assert "[MASKED_NAME]" in result
    assert "[MASKED_DOCUMENT]" in result

@pytest.mark.unit
def test_sanitize_name_with_accents():
    assert "[MASKED_NAME]" in sanitize_text("María José presentó la solicitud.")

@pytest.mark.unit
def test_sanitize_document_with_dots():
    assert sanitize_text("cédula 1.234.567") == "cédula [MASKED_DOCUMENT]"

@pytest.mark.unit
def test_sanitize_document_without_dots():
    assert sanitize_text("CC 1234567") == "CC [MASKED_DOCUMENT]"

@pytest.mark.unit
def test_sanitize_email_and_name_together():
    result = sanitize_text("María José, correo maria@example.com.")
    assert "[MASKED_NAME]" in result
    assert "[MASKED_EMAIL]" in result

@pytest.mark.unit
def test_sanitize_text_without_pii_is_unchanged():
    text = "El trámite fue recibido y será revisado por el área correspondiente."
    assert sanitize_text(text) == text
