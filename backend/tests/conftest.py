import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.core.database import Base, get_db
from app.main import app
from app.models.area import Area
from app.schemas.classification import TicketClassification, AreaCode
from app.services.classifier import ClassificationOutcome
from app.models.ticket import TicketType, TicketPriority

# Postgres required due to postgresql.UUID and JSONB in models
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:admin@localhost:5432/ticket_db")

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def seed_areas(db_session):
    areas = [
        Area(code="ATENCION_USUARIO", name="Atención al Usuario", description="Recepción general", is_active=True, is_default=True),
        Area(code="FACTURACION", name="Facturación", description="Cobros", is_active=True, is_default=False),
        Area(code="SOPORTE_TECNICO", name="Soporte Técnico", description="Soporte", is_active=True, is_default=False),
    ]
    db_session.add_all(areas)
    db_session.commit()
    return areas

@pytest.fixture
def sample_claimant_payload():
    from tests.fixtures.payloads import sample_claimant_payload
    return sample_claimant_payload.copy()

@pytest.fixture
def sample_ticket_payload():
    from tests.fixtures.payloads import sample_ticket_payload
    import copy
    return copy.deepcopy(sample_ticket_payload)

@pytest.fixture
def mock_openai_classification(mocker):
    def _mock(classification_kwargs=None):
        if classification_kwargs is None:
            classification_kwargs = {
                "ticket_type": TicketType.PETITION,
                "priority": TicketPriority.MEDIUM,
                "responsible_area": AreaCode.ATENCION_USUARIO,
                "decision_justification": "Mocked justification that is longer than 10 characters."
            }
        mock_outcome = ClassificationOutcome(
            classification=TicketClassification(**classification_kwargs),
            raw_response={"mock": "data"},
            tokens_used=100,
            latency_ms=150,
            confidence=0.99
        )
        return mocker.patch("app.services.ticket_service.classify_ticket_text", return_value=mock_outcome)
    return _mock

