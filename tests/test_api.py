import pytest
from fastapi.testclient import TestClient

import api
import config


@pytest.fixture
def client(fake_llm, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "")
    monkeypatch.setattr(api, "limiter", api.RateLimiter(100))
    api.sessions.sessions.clear()
    return TestClient(api.app)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_returns_structured_reply(client):
    r = client.post("/v1/chat", json={"user_id": "priya-1", "message": "I feel homesick, I miss amma"})
    assert r.status_code == 200
    body = r.json()
    assert body["reply"] and body["emotion"] == "sad" and body["culture"] == "homesickness"


def test_validation(client):
    assert client.post("/v1/chat", json={"user_id": "bad id!", "message": "hi"}).status_code == 422
    assert client.post("/v1/chat", json={"user_id": "u1", "message": ""}).status_code == 422


def test_api_key_required_when_configured(client, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "s3cret")
    assert client.post("/v1/chat", json={"user_id": "u1", "message": "hi"}).status_code == 401
    ok = client.post("/v1/chat", json={"user_id": "u1", "message": "hi"}, headers={"X-API-Key": "s3cret"})
    assert ok.status_code == 200


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(api, "limiter", api.RateLimiter(2))
    for _ in range(2):
        assert client.post("/v1/chat", json={"user_id": "u1", "message": "hi"}).status_code == 200
    assert client.post("/v1/chat", json={"user_id": "u1", "message": "hi"}).status_code == 429


def test_stream_endpoint(client):
    with client.stream("POST", "/v1/chat/stream", json={"user_id": "u1", "message": "hello"}) as r:
        text = "".join(r.iter_text())
    assert "event: meta" in text and "event: token" in text and "event: done" in text


def test_mood_and_delete_my_data(client):
    client.post("/v1/chat", json={"user_id": "u9", "message": "My name is Priya and I am so happy"})
    assert client.get("/v1/users/u9/mood").json()["history"][0]["emotion"] == "happy"
    assert client.get("/v1/users/u9/greeting").json()["reply"].startswith("Welcome back Priya")
    assert client.delete("/v1/users/u9").json()["deleted_records"] >= 2
    assert client.get("/v1/users/u9/mood").json()["history"] == []
