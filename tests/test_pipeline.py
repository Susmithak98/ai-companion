from core.pipeline import Session, respond, respond_stream


def test_normal_turn_runs_every_agent(fake_llm):
    s = Session(user_id="u1")
    r = respond(s, "My name is Priya and I feel so homesick, I miss amma")
    assert r.reply == "I'm here for you. Tell me more?"
    assert r.emotion == "sad" and r.culture == "homesickness" and r.crisis_level == "normal"
    prompt = fake_llm.prompts[-1]
    assert "Priya" in prompt and "misses home" in prompt and "very gentle" in prompt
    assert len(s.history) == 2


def test_crisis_never_reaches_llm(fake_llm):
    r = respond(Session(user_id="u1"), "I want to end my life")
    assert r.crisis_level == "crisis" and "988" in r.reply
    assert fake_llm.prompts == []


def test_exercise_offered_once_after_two_hard_messages(fake_llm):
    s = Session(user_id="u1")
    assert respond(s, "I'm so stressed about work").exercise is None
    second = respond(s, "Still overwhelmed with deadlines")
    assert second.exercise and second.exercise["name"] == "Box Breathing"
    assert respond(s, "so stressed again").exercise is None


def test_goodbye_ends_session(fake_llm):
    assert respond(Session(), "ok bye for now").ended


def test_stream_events(fake_llm):
    events = list(respond_stream(Session(user_id="u1"), "I got the job, so happy!"))
    assert events[0]["type"] == "meta" and events[0]["emotion"] == "happy"
    assert "".join(e["text"] for e in events if e["type"] == "token") == "I'm here for you. Tell me more?"
    assert events[-1] == {"type": "done", "reply": "I'm here for you. Tell me more?"}
