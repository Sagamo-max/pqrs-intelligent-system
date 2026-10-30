import pytest

from app.core.security import hash_password
from app.models.funcionario import Funcionario, FuncionarioRole
from app.models.refresh_token import RefreshToken


def _create_user(db_session, username, role, password="secret", **kwargs):
    user = Funcionario(
        username=username,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
        **kwargs,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _login(client, username):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "secret"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.integration
def test_login_success(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    response = auth_client.post(
        "/api/auth/login",
        json={"username": "master", "password": "secret"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["role"] == "MASTER"


@pytest.mark.integration
def test_login_invalid_password(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    response = auth_client.post(
        "/api/auth/login",
        json={"username": "master", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


@pytest.mark.integration
def test_login_nonexistent_user(auth_client):
    response = auth_client.post(
        "/api/auth/login",
        json={"username": "missing", "password": "secret"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


@pytest.mark.integration
def test_login_inactive_user(auth_client, db_session):
    user = _create_user(db_session, "inactive", FuncionarioRole.MASTER)
    user.is_active = False
    response = auth_client.post(
        "/api/auth/login",
        json={"username": "inactive", "password": "secret"},
    )
    assert response.status_code == 403


@pytest.mark.integration
def test_me_with_valid_token(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    headers = _login(auth_client, "master")
    response = auth_client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "master"
    assert response.json()["role"] == "MASTER"


@pytest.mark.integration
def test_me_without_token(auth_client):
    assert auth_client.get("/api/auth/me").status_code == 401


@pytest.mark.integration
def test_create_funcionario_as_master(auth_client, db_session, seed_areas):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    headers = _login(auth_client, "master")
    response = auth_client.post(
        "/api/auth/funcionarios",
        headers=headers,
        json={
            "username": "analista",
            "password": "secret",
            "role": "ANALISTA",
            "area_id": str(seed_areas[0].id),
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "ANALISTA"


@pytest.mark.integration
def test_create_funcionario_as_analista_forbidden(auth_client, db_session, seed_areas):
    _create_user(
        db_session,
        "analyst",
        FuncionarioRole.ANALISTA,
        area_id=seed_areas[0].id,
    )
    headers = _login(auth_client, "analyst")
    response = auth_client.post(
        "/api/auth/funcionarios",
        headers=headers,
        json={"username": "other", "password": "secret", "role": "MASTER"},
    )
    assert response.status_code == 403


@pytest.mark.integration
def test_create_analista_without_area_fails(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    headers = _login(auth_client, "master")
    response = auth_client.post(
        "/api/auth/funcionarios",
        headers=headers,
        json={"username": "analyst", "password": "secret", "role": "ANALISTA"},
    )
    assert response.status_code == 400


@pytest.mark.integration
def test_create_supervisor_with_area_fails(auth_client, db_session, seed_areas):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    headers = _login(auth_client, "master")
    response = auth_client.post(
        "/api/auth/funcionarios",
        headers=headers,
        json={
            "username": "supervisor",
            "password": "secret",
            "role": "SUPERVISOR",
            "area_id": str(seed_areas[0].id),
        },
    )
    assert response.status_code == 400


@pytest.mark.integration
def test_create_duplicate_username(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    headers = _login(auth_client, "master")
    payload = {"username": "duplicate", "password": "secret", "role": "MASTER"}
    first = auth_client.post(
        "/api/auth/funcionarios",
        headers=headers,
        json=payload,
    )
    second = auth_client.post(
        "/api/auth/funcionarios",
        headers=headers,
        json=payload,
    )
    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.integration
def test_refresh_rotates_token(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    login = auth_client.post(
        "/api/auth/login",
        json={"username": "master", "password": "secret"},
    )
    old_refresh = login.json()["refresh_token"]

    response = auth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    )

    assert response.status_code == 200
    assert response.json()["refresh_token"] != old_refresh
    assert auth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    ).status_code == 401


@pytest.mark.integration
def test_refresh_reuse_detection(auth_client, db_session):
    user = _create_user(db_session, "master", FuncionarioRole.MASTER)
    login = auth_client.post(
        "/api/auth/login",
        json={"username": "master", "password": "secret"},
    )
    old_refresh = login.json()["refresh_token"]
    rotated = auth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    new_refresh = rotated.json()["refresh_token"]

    assert auth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    ).status_code == 401
    assert auth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": new_refresh},
    ).status_code == 401
    assert (
        db_session.query(RefreshToken)
        .filter(RefreshToken.funcionario_id == user.id)
        .count()
        == 0
    )


@pytest.mark.integration
def test_logout_invalidates_refresh(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    login = auth_client.post(
        "/api/auth/login",
        json={"username": "master", "password": "secret"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = auth_client.post(
        "/api/auth/logout",
        headers=headers,
        json={"refresh_token": login.json()["refresh_token"]},
    )

    assert response.status_code == 200
    assert auth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    ).status_code == 401


@pytest.mark.integration
def test_logout_blacklists_access_token(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)
    login = auth_client.post(
        "/api/auth/login",
        json={"username": "master", "password": "secret"},
    )
    access_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    assert auth_client.post(
        "/api/auth/logout",
        headers=headers,
        json={"refresh_token": login.json()["refresh_token"]},
    ).status_code == 200
    assert auth_client.get("/api/auth/me", headers=headers).status_code == 401


@pytest.mark.integration
def test_rate_limit_login(auth_client, db_session):
    _create_user(db_session, "master", FuncionarioRole.MASTER)

    for _ in range(5):
        response = auth_client.post(
            "/api/auth/login",
            json={"username": "master", "password": "wrong"},
        )
        assert response.status_code == 401

    response = auth_client.post(
        "/api/auth/login",
        json={"username": "master", "password": "wrong"},
    )
    assert response.status_code == 429
    assert response.json()["detail"] == "Demasiados intentos. Intente más tarde."
