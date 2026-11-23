import json

import requests

from core import brain


def test_prompt_includes_every_agent():
    prompt = brain.build_prompt(
        "I miss home", emotion="sad",
        history=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        memory_context="User's name is Priya.", mood_summary="Recent mood: mostly sad (3/4 times).",
        culture_hint="User misses home and family.")
    for part in ["You are Aira", "Priya", "mostly sad", "very gentle", "misses home", "User: hi", "Aira: hello",
                 "User: I miss home\nAira:"]:
        assert part in prompt


class FakeResponse:
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


def test_stream_reply_speaks_each_sentence(monkeypatch):
    monkeypatch.setattr(brain.requests, "post", lambda *a, **k: FakeResponse(["I'm here", " for you.", " Tell me", " more?"]))
    spoken = []
    reply = brain.stream_reply("prompt", on_sentence=spoken.append)
    assert reply == "I'm here for you. Tell me more?"
    assert spoken == ["I'm here for you.", "Tell me more?"]


def test_stream_reply_falls_back_when_llm_is_down(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("ollama down")
    monkeypatch.setattr(brain.requests, "post", boom)
    assert brain.stream_reply("prompt") == brain.FALLBACK
