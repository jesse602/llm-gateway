import respx
from fastapi.testclient import TestClient
from httpx import Response

from app.config import settings
from app.main import app

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-key"}


@respx.mock
def test_chat_completions_proxies_to_ollama():
    respx.post(f"{settings.ollama_base_url}/v1/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "hi"}}]})
    )

    resp = client.post(
        "/v1/chat/completions",
        headers=AUTH,
        json={"model": "llama3.1:8b", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "hi"


@respx.mock
def test_upstream_unreachable_returns_502():
    respx.post(f"{settings.ollama_base_url}/v1/chat/completions").mock(
        side_effect=__import__("httpx").ConnectError("refused")
    )

    resp = client.post(
        "/v1/chat/completions",
        headers=AUTH,
        json={"model": "llama3.1:8b", "messages": []},
    )

    assert resp.status_code == 502
