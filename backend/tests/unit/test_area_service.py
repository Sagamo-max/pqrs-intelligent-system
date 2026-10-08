import pytest
from unittest.mock import MagicMock
from app.services.area_service import resolve_area, get_default
from app.models.area import Area

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.mark.unit
def test_resolve_area_valid_code(mock_db_session):
    valid_area = Area(code="VALID", is_active=True, is_default=False)
    mock_db_session.scalar.return_value = valid_area
    
    result = resolve_area(mock_db_session, "VALID")
    assert result == valid_area

@pytest.mark.unit
def test_resolve_area_inexistent_code_falls_back_to_default(mock_db_session):
    default_area = Area(code="ATENCION_USUARIO", is_active=True, is_default=True)
    mock_db_session.scalar.side_effect = [None, default_area]
    
    result = resolve_area(mock_db_session, "INVALID")
    assert result == default_area

@pytest.mark.unit
def test_resolve_area_none_code_falls_back_to_default(mock_db_session):
    default_area = Area(code="ATENCION_USUARIO", is_active=True, is_default=True)
    mock_db_session.scalar.return_value = default_area
    
    result = resolve_area(mock_db_session, None)
    assert result == default_area

@pytest.mark.unit
def test_resolve_area_points_to_default(mock_db_session):
    default_area = Area(code="ATENCION_USUARIO", is_active=True, is_default=True)
    mock_db_session.scalar.return_value = default_area
    
    result = resolve_area(mock_db_session, "ATENCION_USUARIO")
    assert result == default_area

@pytest.mark.unit
def test_get_default_raises_error_if_no_default(mock_db_session):
    mock_db_session.scalar.return_value = None
    with pytest.raises(RuntimeError, match="No default area configured"):
        get_default(mock_db_session)

