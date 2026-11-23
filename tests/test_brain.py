import requests

from core import brain


def test_prompt_includes_every_agent():
    prompt = brain.build_prompt(
        "I miss home", emotion="sad",
        history=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        memory_context="User's name is Priya.", mood_summary="Recent mood: mostly sad (3/4 times).",
        culture_hint="User misses home and family.")
    for part in ["You are Aira", "Priya", "mostly sad", "very gentle", "misses home", "User: hi",
                 "Aira: hello", "User: I miss home\nAira:"]:
        assert part in prompt


def test_stream_reply_speaks_each_sentence(fake_llm):
    spoken = []
    assert brain.stream_reply("prompt", on_sentence=spoken.append) == "I'm here for you. Tell me more?"
    assert spoken == ["I'm here for you.", "Tell me more?"]


def test_retries_then_falls_back(monkeypatch):
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise requests.ConnectionError("ollama down")
    monkeypatch.setattr(brain.requests, "post", boom)
    monkeypatch.setattr(brain, "LLM_RETRIES", 2)
    monkeypatch.setattr(brain.time, "sleep", lambda s: None)
    assert brain.stream_reply("prompt") == brain.FALLBACK
    assert len(calls) == 3
