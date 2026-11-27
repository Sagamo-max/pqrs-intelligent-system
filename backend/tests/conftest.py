import os

import pytest
from dotenv import load_dotenv

load_dotenv()  

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_deps import get_current_user
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.area import Area
from app.models.funcionario import Funcionario, FuncionarioRole
from app.models.ticket import TicketPriority, TicketType
from app.schemas.classification import AreaCode, TicketClassification
from app.services.classifier import ClassificationOutcome


_TEST_URL = os.getenv("TEST_DATABASE_URL")
_DEV_URL = os.getenv("DATABASE_URL")

if not _TEST_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is not set. Tests require a dedicated Postgres "
        "database (SQLite is not supported because models use JSONB and "
        "postgresql.UUID). Add TEST_DATABASE_URL to your .env, e.g.:\n"
        "  TEST_DATABASE_URL=postgresql+psycopg://postgres:admin@localhost:5432/ticket_db_test"
    )

if _DEV_URL and _TEST_URL == _DEV_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL must be different from DATABASE_URL. "
        "Refusing to run tests against the development database."
    )

TEST_DATABASE_URL = _TEST_URL


@pytest.fixture(autouse=True)
def disable_companero_api_for_tests(mocker):
    """Prevent integration tests from sending requests to the real API."""
    mocker.patch.object(settings, "COMPANERO_API_ENABLED", False)


# ---------------------------------------------------------------------------
# SAFETY GUARDS
# ---------------------------------------------------------------------------
# This conftest MUST run against a dedicated test database. It used to fall
# back to the development database URL, which caused `pytest` to DROP the
# development database. We now require TEST_DATABASE_URL to be set and to be
# different from DATABASE_URL.

_TEST_URL = os.getenv("TEST_DATABASE_URL")
_DEV_URL = os.getenv("DATABASE_URL")

if not _TEST_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is not set. Tests require a dedicated Postgres "
        "database (SQLite is not supported because models use JSONB and "
        "postgresql.UUID). Add TEST_DATABASE_URL to your .env, e.g.:\n"
        "  TEST_DATABASE_URL=postgresql+psycopg://postgres:admin@localhost:5432/ticket_db_test"
    )

if _DEV_URL and _TEST_URL == _DEV_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL must be different from DATABASE_URL. "
        "Refusing to run tests against the development database."
    )

TEST_DATABASE_URL = _TEST_URL


# ---------------------------------------------------------------------------
# ENGINE / SESSION
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL, future=True)
    
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(bind=engine)
    yield engine
    
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()



@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# FASTAPI CLIENT
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    test_user = Funcionario(role=FuncionarioRole.MASTER, is_active=True)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    app.dependency_overrides.pop(get_current_user, None)
    return client


# ---------------------------------------------------------------------------
# DOMAIN FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_areas(db_session):
    areas = [
        Area(
            code="ATENCION_USUARIO",
            name="Atención al Usuario",
            description="Recepción general",
            is_active=True,
            is_default=True,
        ),
        Area(
            code="FACTURACION",
            name="Facturación",
            description="Cobros",
            is_active=True,
            is_default=False,
        ),
        Area(
            code="SOPORTE_TECNICO",
            name="Soporte Técnico",
            description="Soporte",
            is_active=True,
            is_default=False,
        ),
    ]
    db_session.add_all(areas)
    db_session.flush()  
    return areas


@pytest.fixture
def sample_claimant_payload():
    from tests.fixtures.payloads import sample_claimant_payload
    return sample_claimant_payload.copy()


@pytest.fixture
def sample_ticket_payload():
    import copy

    from tests.fixtures.payloads import sample_ticket_payload
    return copy.deepcopy(sample_ticket_payload)


@pytest.fixture
def mock_openai_classification(mocker):
    def _mock(classification_kwargs=None):
        default_classification = {
            "ticket_type": TicketType.PETITION,
            "priority": TicketPriority.MEDIUM,
            "responsible_area": AreaCode.ATENCION_USUARIO,
            "decision_justification": (
                "Mocked justification that is longer than 10 characters."
            ),
        }
        if classification_kwargs is not None:
            default_classification.update(classification_kwargs)
        mock_outcome = ClassificationOutcome(
            classification=TicketClassification(**default_classification),
            source="openai",
            raw_response={"mock": "data"},
            tokens_used=100,
            latency_ms=150,
            confidence=0.99,
        )
        return mocker.patch(
            "app.services.ticket_service.classify_ticket_text",
            return_value=mock_outcome,
        )

    return _mock