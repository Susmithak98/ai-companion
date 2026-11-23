# Aira · Empathetic AI Companion

[![CI](https://github.com/Susmithak98/ai-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/Susmithak98/ai-companion/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Aira listens, understands how you feel, remembers what matters to you and responds like a warm Indian friend who understands family pressure, homesickness, arranged marriages and NRI life. She runs on a **local LLM**, so conversations never leave your machine. Use her as a **voice companion** on your laptop, or deploy her as a **REST API** for web and mobile apps.

**▶ Live demo:** https://susmithak98.github.io/ai-companion/

## Architecture

```
                    ┌───────────────────── core/pipeline.py ─────────────────────┐
 voice / text  ──►  │ 🚨 crisis check → 💡 emotion → 📊 mood → 🧠 memory → 🇮🇳 culture │ ──► 🤖 Ollama (phi3:mini)
 (main.py)          │                → 🧘 wellness → prompt                       │      streamed, retried
 REST / SSE    ──►  └──────────────────────────┬──────────────────────────────────┘
 (api.py)                                      ▼
                                    storage.py · SQLite (per-user memory + mood)
```

| Module | Responsibility |
|---|---|
| `core/pipeline.py` | One conversation pipeline shared by the CLI and the API; returns a structured `TurnResult` |
| `agents.py` | Memory, Mood Tracker, Crisis Detection, Wellness and Indian Culture agents |
| `core/brain.py` | Prompt building and Ollama client with timeouts, retries/backoff and graceful fallback |
| `core/emotion.py` | Emotion detection (whole-word keywords plus sentiment fallback) |
| `storage.py` | SQLite (WAL) per-user storage with `delete_user()` for privacy requests |
| `api.py` | FastAPI service: chat, SSE streaming, mood, delete-my-data, health/readiness, API key, rate limit |
| `main.py` | CLI with voice, `--text` and `--mute` modes |
| `core/listener.py` · `transcriber.py` · `speaker.py` | Voice I/O: VAD recording, Whisper STT, pyttsx3 TTS (lazy-loaded) |
| `config.py` | Every setting comes from an `AIRA_*` environment variable, validated at startup |
| `logging_setup.py` | Plain or JSON logs; message text is never logged |

## Quick start

### 1. Voice companion (local)

```bash
ollama pull phi3:mini                      # install Ollama first: https://ollama.com
git clone https://github.com/Susmithak98/ai-companion.git && cd ai-companion
python -m venv venv && venv\Scripts\activate     # macOS/Linux: source venv/bin/activate
pip install -e ".[voice]"
aira              # speak naturally, say "bye" to exit
aira --text       # type instead (no microphone needed)
```

Whisper needs [ffmpeg](https://ffmpeg.org). If it isn't on PATH, set `AIRA_FFMPEG_DIR=C:\ffmpeg\bin`.

### 2. REST API with Docker (Ollama included)

```bash
cp .env.example .env               # set AIRA_API_KEY
docker compose up -d               # starts Ollama, pulls phi3:mini, starts the API on :8080
```

Interactive API docs: **http://localhost:8080/docs**

```bash
curl -X POST http://localhost:8080/v1/chat \
  -H "X-API-Key: change-me" -H "Content-Type: application/json" \
  -d '{"user_id": "priya-1", "message": "I miss home so much today"}'
```

```json
{"reply": "Oh Priya, missing home is so hard. What do you miss most?",
 "emotion": "sad", "crisis_level": "normal", "culture": "homesickness",
 "exercise": null, "low_mood_note": null, "ended": false}
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/chat` | One reply with emotion, crisis level, cultural context and an optional exercise |
| `POST` | `/v1/chat/stream` | Server-sent events: `meta`, then `token`s, then `done` |
| `GET` | `/v1/users/{id}/greeting` | Personalized greeting (uses memory) |
| `GET` | `/v1/users/{id}/mood` | Mood summary and history |
| `DELETE` | `/v1/users/{id}` | Erase all stored data for a user |
| `GET` | `/health` · `/ready` | Liveness · readiness (is the LLM reachable?) |

## Safety and privacy

- **Crisis first:** every message is checked for crisis language before anything else. Those messages never reach the LLM; Aira replies with fixed, reviewed text pointing to **988** (US) and **Tele MANAS 14416** (India).
- **Data minimization:** only the detected emotion is stored by default, never what the user said (`AIRA_STORE_EXCERPTS=false`). Crisis messages are never stored.
- **Right to erasure:** `DELETE /v1/users/{id}` removes a user's memory and mood history.
- **No conversation text in logs.** Logs contain only metadata (path, status, latency, emotion).
- **Prompt-injection resistant system prompt**, input length limits and user-id validation.
- **API key auth** (`X-API-Key`) and **per-user rate limiting** for the hosted API.

See [SECURITY.md](SECURITY.md).

## Configuration

| Variable | Default | |
|---|---|---|
| `AIRA_OLLAMA_URL` | `http://localhost:11434` | LLM server |
| `AIRA_OLLAMA_MODEL` | `phi3:mini` | Any Ollama model |
| `AIRA_LLM_TIMEOUT` / `AIRA_LLM_RETRIES` | `60` / `2` | Resilience |
| `AIRA_API_KEY` | *(empty)* | Required header for the API when set |
| `AIRA_RATE_LIMIT_PER_MINUTE` | `30` | Per user |
| `AIRA_CORS_ORIGINS` | *(empty)* | Comma-separated origins for browser apps |
| `AIRA_DATA_DIR` / `AIRA_DB_PATH` | `./data` / `./data/aira.db` | Storage |
| `AIRA_STORE_EXCERPTS` | `false` | Store the first 100 characters of messages |
| `AIRA_LOG_JSON` / `AIRA_LOG_LEVEL` | `false` / `INFO` | Logging |
| `AIRA_WHISPER_MODEL` · `AIRA_FFMPEG_DIR` | `base` · *(PATH)* | Voice mode |

## Development

```bash
pip install -r requirements-dev.txt
ruff check .        # lint
pytest -q           # 24 tests; no microphone, GPU or LLM needed
```

CI runs lint and tests on Python 3.10 and 3.12, builds the Docker image, smoke-tests it, and publishes `ghcr.io/susmithak98/aira-api`.

## Production notes

- The API keeps short-term conversation context in memory and rate-limits in memory. For several replicas, move both to Redis or an API gateway.
- SQLite in WAL mode handles a single instance well. For multi-instance deployments, point `storage.py` at PostgreSQL.
- Run behind HTTPS (a reverse proxy or cloud load balancer).

---

> Aira is a supportive companion, **not a therapist or a medical service**. If you are in crisis, call or text **988** (US) or **14416** (India).

Built by **Susmitha Kotharu** · MIT License
