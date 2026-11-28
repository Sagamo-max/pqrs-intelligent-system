from fastapi.testclient import TestClient

from app.main import app, get_cors_origins


def test_get_cors_origins_parses_comma_separated_env(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        " https://frontend.up.railway.app , http://localhost:5173 , ",
    )
    assert get_cors_origins() == [
        "https://frontend.up.railway.app",
        "http://localhost:5173",
    ]


def test_cors_allows_configured_origin_and_blocks_unknown():
    client = TestClient(app)

    allowed = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert allowed.headers.get("access-control-allow-credentials") == "true"

    preflight = client.options(
        "/api/v1/pqrs/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "http://localhost:5173"

    blocked = client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert blocked.status_code == 200
    assert "access-control-allow-origin" not in blocked.headers
