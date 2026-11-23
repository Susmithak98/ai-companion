"""The conversation pipeline shared by the CLI and the API.

    safety (crisis) -> emotion -> mood log -> memory -> culture -> wellness -> LLM

Every turn returns a structured TurnResult, so callers decide how to present it
(speak it, print it, or send it as JSON).
"""
import logging
import re
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field
from typing import Optional

import agents
import config
from core import brain
from core.emotion import detect_emotion

log = logging.getLogger("aira.pipeline")
EXIT_WORDS = re.compile(r"\b(goodbye|bye|exit|quit)\b", re.I)
LOW_MOOD_NOTE = ("I noticed you have been feeling down a lot lately. I care about you. "
                 "Please consider talking to someone you trust.")


@dataclass
class TurnResult:
    reply: str
    emotion: str
    crisis_level: str = "normal"
    culture: Optional[str] = None
    exercise: Optional[dict] = None
    low_mood_note: Optional[str] = None
    ended: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Session:
    """Per-conversation state. Long-term memory and mood live in storage, keyed by user_id."""
    user_id: str = agents.LOCAL_USER
    history: list[dict] = field(default_factory=list)
    exercise_offered: bool = False
    warned_low_mood: bool = False

    def remember(self, user_text: str, reply: str) -> None:
        self.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}]
        self.history = self.history[-20:]


def greeting(user_id: str = agents.LOCAL_USER) -> str:
    agents.update_last_seen(user_id)
    name = agents.load_memory(user_id)["user_name"]
    return (f"Welcome back {name}. I am Aira. How are you feeling today?" if name
            else "Hi there. I am Aira. I am here for you. Just start talking.")


def _prepare(session: Session, text: str):
    """Run every agent before the LLM. Returns (early_result, prompt, partial_result)."""
    text = text.strip()[: config.MAX_MESSAGE_CHARS]
    uid = session.user_id

    if EXIT_WORDS.search(text):
        bye = TurnResult("Take care of yourself. I am always here for you. Goodbye.", "neutral", ended=True)
        return bye, None, None

    level = agents.check_crisis(text)
    if level != "normal":
        reply = agents.get_crisis_response(level)
        agents.log_mood("crisis" if level == "crisis" else "sad", "", uid)   # never store crisis text
        session.remember(text, reply)
        log.warning("Crisis language detected", extra={"user": uid, "crisis": level})
        return TurnResult(reply, "sad", crisis_level=level), None, None

    emotion = detect_emotion(text)
    agents.log_mood(emotion, text, uid)
    streak = agents.check_consecutive_sad(uid)
    agents.extract_facts(text, uid)
    scenario, culture_hint = agents.detect_indian_scenario(text)

    result = TurnResult(reply="", emotion=emotion, culture=scenario)
    if streak >= 5 and not session.warned_low_mood:
        session.warned_low_mood = True
        result.low_mood_note = LOW_MOOD_NOTE
    if agents.should_suggest_exercise(emotion, streak, session.exercise_offered):
        session.exercise_offered = True
        result.exercise = {"intro": agents.get_exercise_intro(emotion), **agents.get_exercise(emotion)}

    prompt = brain.build_prompt(text, emotion, session.history, agents.get_memory_context(uid),
                                agents.get_mood_summary(uid), culture_hint)
    log.info("Turn prepared", extra={"user": uid, "emotion": emotion})
    return None, prompt, result


def respond(session: Session, text: str, on_sentence: Optional[Callable[[str], None]] = None) -> TurnResult:
    early, prompt, result = _prepare(session, text)
    if early:
        return early
    result.reply = brain.stream_reply(prompt, on_sentence=on_sentence)
    session.remember(text.strip(), result.reply)
    return result


def respond_stream(session: Session, text: str) -> Iterator[dict]:
    """Yield {'type': 'meta'|'token'|'done', ...} events for streaming clients (SSE)."""
    early, prompt, result = _prepare(session, text)
    if early:
        yield {"type": "meta", **early.to_dict()}
        yield {"type": "token", "text": early.reply}
        yield {"type": "done", "reply": early.reply}
        return
    meta = result.to_dict()
    meta.pop("reply")
    yield {"type": "meta", **meta}
    reply = ""
    try:
        for token in brain.stream_tokens(prompt):
            reply += token
            yield {"type": "token", "text": token}
    except Exception as exc:  # LLM down mid-stream: finish politely
        log.error("Stream failed: %s", exc)
        if not reply:
            reply = brain.FALLBACK
            yield {"type": "token", "text": reply}
    reply = reply.strip() or brain.FALLBACK
    session.remember(text.strip(), reply)
    yield {"type": "done", "reply": reply}
