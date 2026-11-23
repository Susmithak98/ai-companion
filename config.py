"""Central settings for Aira. Every value can be overridden with an AIRA_* environment variable."""
import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        raise SystemExit(f"Config error: {name} must be an integer") from None


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        raise SystemExit(f"Config error: {name} must be a number") from None


# Local LLM served by Ollama
OLLAMA_URL = os.getenv("AIRA_OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("AIRA_OLLAMA_MODEL", "phi3:mini")
LLM_TEMPERATURE = _float("AIRA_TEMPERATURE", 0.8)
LLM_MAX_TOKENS = _int("AIRA_MAX_TOKENS", 80)
LLM_TIMEOUT_SECONDS = _float("AIRA_LLM_TIMEOUT", 60)
LLM_RETRIES = _int("AIRA_LLM_RETRIES", 2)

# Speech (voice mode only)
WHISPER_MODEL = os.getenv("AIRA_WHISPER_MODEL", "base")
FFMPEG_DIR = os.getenv("AIRA_FFMPEG_DIR", "")
SAMPLE_RATE = 16000
MAX_RECORD_SECONDS = _int("AIRA_MAX_RECORD_SECONDS", 30)
VOICE_RATE = _int("AIRA_VOICE_RATE", 165)
VOICE_PREFERENCE = ("zira", "female", "heera", "samantha")

# Storage: one SQLite file holds every user's memory and mood history (git-ignored)
DATA_DIR = os.getenv("AIRA_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
DB_PATH = os.getenv("AIRA_DB_PATH", os.path.join(DATA_DIR, "aira.db"))
OUTPUT_DIR = os.path.join(DATA_DIR, "recordings")
# Privacy: by default only the emotion is stored, never what the user said
STORE_EXCERPTS = os.getenv("AIRA_STORE_EXCERPTS", "false").lower() == "true"

# Conversation
HISTORY_TURNS = 6
MAX_FACTS = 20
MAX_MESSAGE_CHARS = _int("AIRA_MAX_MESSAGE_CHARS", 2000)

# API service
API_KEY = os.getenv("AIRA_API_KEY", "")                 # empty = no auth (local use only)
RATE_LIMIT_PER_MINUTE = _int("AIRA_RATE_LIMIT_PER_MINUTE", 30)
CORS_ORIGINS = [o.strip() for o in os.getenv("AIRA_CORS_ORIGINS", "").split(",") if o.strip()]
LOG_LEVEL = os.getenv("AIRA_LOG_LEVEL", "INFO").upper()
LOG_JSON = os.getenv("AIRA_LOG_JSON", "false").lower() == "true"
