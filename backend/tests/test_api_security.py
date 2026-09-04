from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import models
from backend.app.auth.utils import create_access_token, hash_password
from backend.app.dependencies import get_db
from backend.app.main import app
from config import settings


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine)
    models.Base.metadata.create_all(engine)

    def override_db():
        database = session_factory()
        try:
            yield database
        finally:
            database.close()

    monkeypatch.setattr(settings, "DEMO_MODE", True)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client, session_factory
    app.dependency_overrides.clear()
    models.Base.metadata.drop_all(engine)
    engine.dispose()


def demo_session(client: TestClient) -> str:
    response = client.post("/auth/demo")
    assert response.status_code == 200
    return response.json()["access_token"]


def test_demo_login_issues_a_valid_read_only_session(client):
    test_client, _ = client
    token = demo_session(test_client)

    response = test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "Recruiter Demo"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/resources"),
        ("POST", "/policies"),
        ("POST", "/scans"),
        ("PATCH", "/remediations/1"),
    ],
)
def test_demo_session_rejects_mutations(client, method, path):
    test_client, _ = client
    token = demo_session(test_client)

    response = test_client.request(
        method,
        path,
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "The public demo is read-only."}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_invalid_and_expired_tokens_are_rejected(client):
    test_client, session_factory = client
    database = session_factory()
    database.add(
        models.User(
            email="expired@example.com",
            username="Expired User",
            hashed_password=hash_password("not-used-by-this-test"),
        )
    )
    database.commit()
    database.close()
    expired = create_access_token(
        "expired@example.com",
        expires_delta=timedelta(seconds=-1),
    )

    for token in ("not-a-jwt", expired):
        response = test_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_cors_allows_the_frontend_but_not_unknown_origins(client):
    test_client, _ = client
    allowed = test_client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    unknown = test_client.options(
        "/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in unknown.headers


def test_api_responses_include_security_headers(client):
    test_client, _ = client
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["cache-control"] == "no-store"
