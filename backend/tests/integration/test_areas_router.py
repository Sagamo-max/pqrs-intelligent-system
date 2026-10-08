import pytest
import uuid

@pytest.mark.integration
def test_list_areas(client, seed_areas):
    response = client.get("/api/v1/areas/")
    assert response.status_code == 200
    assert len(response.json()) >= 3

@pytest.mark.integration
def test_get_area_valid(client, seed_areas):
    area_id = str(seed_areas[0].id)
    response = client.get(f"/api/v1/areas/{area_id}")
    assert response.status_code == 200
    assert response.json()["code"] == seed_areas[0].code

@pytest.mark.integration
def test_get_area_not_found(client):
    response = client.get(f"/api/v1/areas/{uuid.uuid4()}")
    assert response.status_code == 404

@pytest.mark.integration
def test_create_area(client):
    payload = {
        "code": "NUEVA_AREA",
        "name": "Area de prueba",
        "is_active": True
    }
    response = client.post("/api/v1/areas/", json=payload)
    assert response.status_code == 201
    assert response.json()["code"] == "NUEVA_AREA"

@pytest.mark.integration
def test_create_area_duplicate(client, seed_areas):
    payload = {
        "code": seed_areas[0].code,
        "name": "Duplicate area"
    }
    response = client.post("/api/v1/areas/", json=payload)
    assert response.status_code == 409

@pytest.mark.integration
def test_update_area(client, seed_areas):
    area_id = str(seed_areas[1].id)
    payload = {"name": "Nombre Actualizado"}
    response = client.patch(f"/api/v1/areas/{area_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Nombre Actualizado"

@pytest.mark.integration
@pytest.mark.xfail(reason="SQLite doesn't support Postgres partial unique indexes. Will only fail on real PostgreSQL.")
def test_default_area_is_unique(client, seed_areas):
    payload = {
        "code": "OTRA_DEFAULT",
        "name": "Otra default",
        "is_default": True
    }
    with pytest.raises(Exception):
        # Depending on the DB it might raise IntegrityError
        # In the context of FastAPI TestClient, 500 error will bubble up as Exception
        # because we don't have a broad exception handler in the test client
        client.post("/api/v1/areas/", json=payload)
