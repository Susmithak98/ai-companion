"""Speaker: text-to-speech with pyttsx3 (offline). Falls back to printing when unavailable."""
from config import VOICE_PREFERENCE, VOICE_RATE

_engine = None
enabled = True


def _get_engine():
    global _engine
    if _engine is None:
        import pyttsx3
        _engine = pyttsx3.init()
        _engine.setProperty("rate", VOICE_RATE)
        _engine.setProperty("volume", 1.0)
        for voice in _engine.getProperty("voices"):
            if any(p in voice.name.lower() for p in VOICE_PREFERENCE):
                _engine.setProperty("voice", voice.id)
                break
    return _engine


def speak(text: str, show: bool = True) -> None:
    if not text:
        return
    if show:
        print(f"\nAira: {text}")
    if not enabled:
        return
    try:
        engine = _get_engine()
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:
        print(f"(voice unavailable: {exc})")
