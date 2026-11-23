"""Backwards-compatible entry point: re-exports the pipeline from core/.

Older code did `from aira import record_audio, transcribe, ...`; that still works.
"""
from agents import detect_indian_scenario, extract_facts, get_memory_context, get_mood_summary
from core.brain import build_prompt, stream_reply
from core.emotion import detect_emotion
from core.listener import record_audio
from core.speaker import speak
from core.transcriber import transcribe

__all__ = ["record_audio", "transcribe", "detect_emotion", "get_response", "speak"]


def get_response(user_text, emotion="neutral", history=None, on_sentence=speak):
    """Run every agent, build the prompt and stream Aira's reply (spoken sentence by sentence)."""
    extract_facts(user_text)
    _, culture_hint = detect_indian_scenario(user_text)
    prompt = build_prompt(user_text, emotion, history, get_memory_context(), get_mood_summary(), culture_hint)
    print("\nAira: ", end="", flush=True)

    def say(sentence):
        print(sentence, end=" ", flush=True)
        on_sentence(sentence, show=False) if on_sentence is speak else on_sentence(sentence)
    reply = stream_reply(prompt, on_sentence=say)
    print()
    return reply
