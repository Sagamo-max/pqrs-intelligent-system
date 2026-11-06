import uuid

import pytest

from app.models.organizacion import Organizacion


DEMO_ORGANIZATION_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.fixture
def demo_organization(db_session):
    organization = Organizacion(
        id=DEMO_ORGANIZATION_ID,
        name="Organización Demo",
        slug="demo",
        is_active=True,
    )
    db_session.add(organization)
    db_session.flush()
    return organization


@pytest.mark.integration
def test_get_active_organization(auth_client, demo_organization):
    response = auth_client.get("/api/v1/organizaciones/active?slug=demo")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(DEMO_ORGANIZATION_ID),
        "name": "Organización Demo",
        "slug": "demo",
        "is_active": True,
    }


@pytest.mark.integration
def test_get_active_organization_not_found(client):
    response = client.get("/api/v1/organizaciones/active?slug=missing")

    assert response.status_code == 404


@pytest.mark.integration
def test_get_active_organization_inactive(client, db_session):
    db_session.add(
        Organizacion(
            name="Inactive",
            slug="inactive",
            is_active=False,
        )
    )
    db_session.flush()

    response = client.get("/api/v1/organizaciones/active?slug=inactive")

    assert response.status_code == 404
