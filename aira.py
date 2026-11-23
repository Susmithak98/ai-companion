"""Backwards-compatible imports for older scripts (`from aira import ...`)."""
from core.emotion import detect_emotion  # noqa: F401
from core.listener import record_audio  # noqa: F401
from core.pipeline import Session, respond
from core.speaker import speak  # noqa: F401
from core.transcriber import transcribe  # noqa: F401

_session = Session()


def get_response(user_text, emotion=None, history=None):
    """Old API: returns Aira's reply text for the local user."""
    if history is not None:
        _session.history = list(history)
    return respond(_session, user_text).reply
