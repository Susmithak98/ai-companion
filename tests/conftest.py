import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test gets its own empty SQLite database."""
    import config
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "aira.db"))
    monkeypatch.setattr(config, "STORE_EXCERPTS", False)
    yield


class FakeOllama:
    """Stands in for requests.post to Ollama: streams the given tokens."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.prompts = []

    def __call__(self, url, json=None, **kwargs):  # noqa: A002
        self.prompts.append(json["prompt"])
        return _Resp(self.tokens)


class _Resp:
    def __init__(self, tokens):
        self.lines = [json.dumps({"response": t}).encode() for t in tokens] + [json.dumps({"done": True}).encode()]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        pass

    def iter_lines(self):
        return iter(self.lines)


@pytest.fixture
def fake_llm(monkeypatch):
    from core import brain
    fake = FakeOllama(["I'm here", " for you.", " Tell me", " more?"])
    monkeypatch.setattr(brain.requests, "post", fake)
    monkeypatch.setattr(brain, "LLM_RETRIES", 0)
    return fake
