import os

import pytest
from dotenv import load_dotenv

load_dotenv()  

# Fallback defaults for isolated unit tests when .env is not present
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("AI_MODEL_NAME", "gpt-6-luna")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-jwt-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "unit-test-refresh-secret")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_deps import get_current_user
from app.core.database import Base, get_db
from app.main import app
from app.models.area import Area
from app.models.funcionario import Funcionario, FuncionarioRole
from app.models.ticket import TicketPriority, TicketType
from app.schemas.classification import AreaCode, TicketClassification
from app.services.classifier import ClassificationOutcome


# ---------------------------------------------------------------------------
# SAFETY GUARDS
# ---------------------------------------------------------------------------
# This conftest MUST run against a dedicated test database. It used to fall
# back to the development database URL, which caused `pytest` to DROP the
# development database. We now require TEST_DATABASE_URL to be set and to be
# different from DATABASE_URL inside `db_engine` so unit tests can run without
# Postgres.


def _get_validated_test_database_url() -> str:
    test_url = os.getenv("TEST_DATABASE_URL")
    dev_url = os.getenv("DATABASE_URL")

    if not test_url:
        raise RuntimeError(
            "TEST_DATABASE_URL is not set. Tests require a dedicated Postgres "
            "database (SQLite is not supported because models use JSONB and "
            "postgresql.UUID). Add TEST_DATABASE_URL to your .env, e.g.:\n"
            "  TEST_DATABASE_URL=postgresql+psycopg://postgres:admin@localhost:5432/ticket_db_test"
        )

    if dev_url and test_url == dev_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must be different from DATABASE_URL. "
            "Refusing to run tests against the development database."
        )

    return test_url


# ---------------------------------------------------------------------------
# ENGINE / SESSION
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_engine():
    test_database_url = _get_validated_test_database_url()
    engine = create_engine(test_database_url, future=True)
    
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