"""Brain: builds Aira's prompt from every agent and streams a reply from the local LLM."""
import json

import requests

from config import HISTORY_TURNS, LLM_MAX_TOKENS, LLM_TEMPERATURE, OLLAMA_MODEL, OLLAMA_URL

SYSTEM_PROMPT = """You are Aira, a warm and empathetic AI companion from India.
You naturally understand Indian culture, family dynamics, and the experiences of NRIs.
You speak like a caring friend: warm, supportive, and genuinely interested.
You understand Indian contexts when they come up but never force them.
Keep responses to 2-3 natural sentences. Be present, not repetitive. Never give medical advice."""

EMOTION_HINTS = {
    "sad": "User is sad. Be very gentle and validating.",
    "stressed": "User is stressed. Be calm and reassuring.",
    "angry": "User is frustrated. Acknowledge feelings calmly.",
    "happy": "User is happy. Match their warm energy.",
    "neutral": "Be warm and curious.",
}
FALLBACK = "I am here for you. Can you tell me more?"


def build_prompt(user_text, emotion="neutral", history=None, memory_context="",
                 mood_summary="", culture_hint=None) -> str:
    lines = [SYSTEM_PROMPT]
    if memory_context:
        lines.append(f"[Memory: {memory_context}]")
    if mood_summary:
        lines.append(f"[{mood_summary}]")
    lines.append(f"[{EMOTION_HINTS.get(emotion, EMOTION_HINTS['neutral'])}]")
    if culture_hint:
        lines.append(f"[Cultural context: {culture_hint}]")
    convo = ""
    for msg in (history or [])[-HISTORY_TURNS:]:
        convo += f"{'User' if msg['role'] == 'user' else 'Aira'}: {msg['content']}\n"
    return "\n".join(lines) + f"\n\n{convo}User: {user_text}\nAira:"


def is_ollama_running(timeout: float = 3) -> bool:
    try:
        requests.get(OLLAMA_URL, timeout=timeout)
        return True
    except requests.RequestException:
        return False


def stream_reply(prompt: str, on_sentence=None) -> str:
    """Stream tokens from Ollama. Calls on_sentence(sentence) as soon as each sentence completes."""
    full, sentence = "", ""
    try:
        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True,
                  "options": {"temperature": LLM_TEMPERATURE, "num_predict": LLM_MAX_TOKENS}},
            stream=True, timeout=60,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("response", "")
                full += token
                sentence += token
                if sentence.strip().endswith((".", "!", "?")) and len(sentence.strip()) > 5:
                    if on_sentence:
                        on_sentence(sentence.strip())
                    sentence = ""
                if chunk.get("done"):
                    break
        if sentence.strip() and on_sentence:
            on_sentence(sentence.strip())
        return full.strip() or FALLBACK
    except (requests.RequestException, ValueError) as exc:
        print(f"\nLLM error: {exc}")
        if on_sentence:
            on_sentence(FALLBACK)
        return FALLBACK
