# Aira · AI Voice Companion

A live voice AI companion that listens, understands emotions and responds with empathy, like a warm Indian friend who understands family pressure, homesickness, arranged marriages and NRI life. It runs **100% offline** on your laptop.

**▶ Live demo (browser version):** https://susmithak98.github.io/ai-companion/

## How it works

```
🎙️ Listener ─► 📝 Transcriber ─► 💡 Emotion ─► 🚨 Crisis check ─► 🧠 Memory + 📊 Mood + 🇮🇳 Culture ─► 🤖 Brain (LLM) ─► 🔊 Speaker
  webrtcvad       Whisper          keywords +      safety first     agents.py                           Ollama phi3:mini   pyttsx3
                                    TextBlob                                                              (streamed)
```

## Project structure

| Path | What it does |
|---|---|
| `main.py` | Conversation loop with voice mode, `--text` mode and `--mute` |
| `config.py` | All settings, each one overridable with an `AIRA_*` environment variable |
| `core/listener.py` | Records only while you speak (voice activity detection) |
| `core/transcriber.py` | Offline speech-to-text with Whisper, loaded once on first use |
| `core/emotion.py` | Emotion detection (whole-word keywords, sentiment fallback) |
| `core/brain.py` | Builds the prompt from every agent and streams the reply from Ollama |
| `core/speaker.py` | Offline text-to-speech, spoken sentence by sentence |
| `agents.py` | Memory, Mood Tracker, Crisis Detection, Wellness and Indian Culture agents |
| `aira.py` | Backwards-compatible imports for older scripts |
| `tests/` | 10 pytest tests; no microphone, GPU or LLM needed |
| `index.html` | The browser demo published with GitHub Pages |

## Agents

| Agent | What it does |
|---|---|
| **Memory** | Remembers your name and key facts (family, work, home) |
| **Mood Tracker** | Logs every emotion and summarizes your recent mood |
| **Crisis Detection** | Checked first on every message; responds safely with the 988 Lifeline (US) and Tele MANAS 14416 (India) |
| **Wellness** | Offers a breathing or gratitude exercise after two difficult messages in a row |
| **Indian Culture** | Spots homesickness, family pressure, visa stress, festivals and more, and guides the reply's tone |

Your memory and mood logs are saved in `data/`, which is git-ignored, so your conversations never leave your laptop.

## Setup

```bash
# 1. Install Ollama from https://ollama.com, then:
ollama pull phi3:mini

# 2. Get the code
git clone https://github.com/Susmithak98/ai-companion.git
cd ai-companion
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# 3. Install ffmpeg (needed by Whisper): https://ffmpeg.org
#    If it isn't on your PATH:  set AIRA_FFMPEG_DIR=C:\ffmpeg\bin
```

## Run

```bash
python main.py            # voice mode: just speak, say "bye" to exit
python main.py --text     # type instead of speaking (no microphone needed)
python main.py --mute     # don't speak replies out loud
```

## Test

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Configuration

| Variable | Default |
|---|---|
| `AIRA_OLLAMA_URL` | `http://localhost:11434` |
| `AIRA_OLLAMA_MODEL` | `phi3:mini` |
| `AIRA_WHISPER_MODEL` | `base` |
| `AIRA_FFMPEG_DIR` | *(empty: use PATH)* |
| `AIRA_DATA_DIR` | `./data` |

> Aira is a supportive companion, not a therapist. If you are in crisis, call or text **988** (US) or **14416** (India).
