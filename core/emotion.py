"""Emotion detector: keyword scoring first, sentiment polarity as a fallback."""
import re

KEYWORDS = {
    "sad": ["sad", "unhappy", "depressed", "hopeless", "cry", "lonely", "empty", "worthless",
            "hurt", "grief", "miserable", "heartbroken", "homesick"],
    "stressed": ["stressed", "overwhelmed", "anxious", "worried", "panic", "too much", "pressure",
                 "exhausted", "cant cope", "can't cope", "deadline"],
    "angry": ["angry", "mad", "furious", "frustrated", "hate", "unfair", "sick of", "fed up", "annoyed"],
    "happy": ["happy", "great", "wonderful", "excited", "joyful", "good", "grateful", "love",
              "amazing", "thankful", "blessed"],
}
EMOTIONS = ("happy", "neutral", "stressed", "sad", "angry")


def _contains(text: str, phrase: str) -> bool:
    """Whole-word / whole-phrase match, so 'mad' does not match 'made'."""
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def _polarity(text: str) -> float:
    try:
        from textblob import TextBlob  # optional dependency
        return TextBlob(text).sentiment.polarity
    except Exception:
        return 0.0


def detect_emotion(text: str) -> str:
    if not text or not text.strip():
        return "neutral"
    low = text.lower()
    scores = {e: sum(_contains(low, w) for w in words) for e, words in KEYWORDS.items()}
    scores = {e: s for e, s in scores.items() if s}
    if scores:
        return max(scores, key=scores.get)
    polarity = _polarity(text)
    if polarity < -0.3:
        return "sad"
    if polarity < -0.1:
        return "stressed"
    if polarity > 0.3:
        return "happy"
    return "neutral"
