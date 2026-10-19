import pytest

from app.schemas.classification import AreaCode
from app.services.heuristic_classifier import heuristic_classify


@pytest.mark.unit
def test_heuristic_matches_factura():
    assert heuristic_classify("Necesito corregir mi factura") == AreaCode.FACTURACION


@pytest.mark.unit
def test_heuristic_matches_soporte():
    assert heuristic_classify("La plataforma no funciona y necesito soporte") == AreaCode.SOPORTE_TECNICO


@pytest.mark.unit
def test_heuristic_returns_none_on_tie():
    assert heuristic_classify("Tengo un error en la factura") is None


@pytest.mark.unit
def test_heuristic_returns_none_on_no_match():
    assert heuristic_classify("Solicito información general sobre mi caso") is None


@pytest.mark.unit
def test_heuristic_ignores_accents():
    assert heuristic_classify("Necesito facturación") == heuristic_classify("Necesito facturacion")


@pytest.mark.unit
def test_heuristic_empty_string():
    assert heuristic_classify("") is None
