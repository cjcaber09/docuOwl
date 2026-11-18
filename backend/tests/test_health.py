from fastapi.testclient import TestClient

import app.main
from app.database import database_is_reachable
from app.main import app as owl_app

client = TestClient(owl_app)


def test_test_database_is_reachable():
    assert database_is_reachable() is True


def test_health_says_ok_when_database_is_reachable():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_says_not_ok_when_database_is_down(monkeypatch):
    monkeypatch.setattr(app.main, "database_is_reachable", lambda: False)

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "not ok"}
