from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_auth_rejected():
    resp = client.post("/v1/chat/completions", json={"model": "x", "messages": []})
    assert resp.status_code == 401


def test_bad_key_rejected():
    resp = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer wrong-key"},
        json={"model": "x", "messages": []},
    )
    assert resp.status_code == 401


def test_healthz_requires_no_auth():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
