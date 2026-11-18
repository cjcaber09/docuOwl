from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.csrf import require_same_origin

demo = FastAPI()
demo.middleware("http")(require_same_origin)


@demo.get("/read")
def read() -> dict[str, str]:
    return {"ok": "yes"}


@demo.post("/change")
def change() -> dict[str, str]:
    return {"ok": "yes"}


client = TestClient(demo)


def test_change_from_owl_is_allowed():
    assert client.post("/change", headers={"Origin": "http://localhost:5173"}).status_code == 200


def test_change_from_another_site_is_blocked():
    response = client.post("/change", headers={"Origin": "https://evil.example"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Request blocked: it didn't come from Owl."}


def test_change_without_origin_is_blocked():
    assert client.post("/change").status_code == 403


def test_reading_needs_no_origin():
    assert client.get("/read").status_code == 200
