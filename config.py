"""Central settings for Aira. Override any value with an environment variable."""
import os

# Local LLM served by Ollama
OLLAMA_URL = os.getenv("AIRA_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("AIRA_OLLAMA_MODEL", "phi3:mini")
LLM_TEMPERATURE = float(os.getenv("AIRA_TEMPERATURE", "0.8"))
LLM_MAX_TOKENS = int(os.getenv("AIRA_MAX_TOKENS", "80"))

# Speech
WHISPER_MODEL = os.getenv("AIRA_WHISPER_MODEL", "base")
FFMPEG_DIR = os.getenv("AIRA_FFMPEG_DIR", "")          # e.g. C:\ffmpeg\bin if ffmpeg is not on PATH
SAMPLE_RATE = 16000
MAX_RECORD_SECONDS = int(os.getenv("AIRA_MAX_RECORD_SECONDS", "30"))
VOICE_RATE = int(os.getenv("AIRA_VOICE_RATE", "165"))
VOICE_PREFERENCE = ("zira", "female", "heera", "samantha")

# Where Aira keeps memory, mood logs and recordings (never committed to git)
DATA_DIR = os.getenv("AIRA_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
OUTPUT_DIR = os.path.join(DATA_DIR, "recordings")
MEMORY_FILE = os.path.join(DATA_DIR, "aira_memory.json")
MOOD_FILE = os.path.join(DATA_DIR, "aira_moods.csv")

HISTORY_TURNS = 6          # how many past messages go into the prompt
MAX_FACTS = 20
