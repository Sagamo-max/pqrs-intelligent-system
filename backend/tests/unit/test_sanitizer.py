import pytest
from app.services.sanitizer_service import (
    _OPERATORS,
    mask_ner_patterns,
    mask_regex_patterns,
    sanitize_text,
)


@pytest.mark.unit
def test_all_configured_masks_use_square_brackets():
    for operator in _OPERATORS.values():
        replacement = operator.params["new_value"]
        assert replacement.startswith("[MASKED_")
        assert replacement.endswith("]")
        assert "<MASKED_" not in replacement

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


@pytest.mark.unit
def test_sanitize_cedula_10_digits_with_dots():
    text = "Mi cédula es 1.023.456.789"
    result = sanitize_text(text)
    assert "[MASKED_DOCUMENT]" in result
    assert "1.023.456.789" not in result
    assert ".789" not in result


@pytest.mark.unit
def test_sanitize_phone_with_spaces():
    text = "Mi teléfono es 310 555 7788"
    result = sanitize_text(text)
    assert "[MASKED_PHONE]" in result
    assert "310 555 7788" not in result


@pytest.mark.unit
def test_sanitize_phone_with_country_code():
    text = "Mi teléfono es +57 310 555 7788"
    result = sanitize_text(text)
    assert "[MASKED_PHONE]" in result


@pytest.mark.unit
def test_sanitize_nit():
    text = "El NIT de mi empresa es 900.123.456-7"
    result = sanitize_text(text)
    assert "[MASKED_NIT]" in result
    assert "900.123.456-7" not in result


@pytest.mark.unit
def test_sanitize_multiple_pii():
    text = (
        "Mi nombre es Carlos, mi cédula es 1.023.456.789, "
        "mi teléfono es 310 555 7788 y el NIT es 900.123.456-7"
    )
    result = sanitize_text(text)
    assert "[MASKED_NAME]" in result
    assert "[MASKED_DOCUMENT]" in result
    assert "[MASKED_PHONE]" in result
    assert "[MASKED_NIT]" in result
    assert "Carlos" not in result
    assert "1.023.456.789" not in result
    assert "310 555 7788" not in result
    assert "900.123.456-7" not in result
