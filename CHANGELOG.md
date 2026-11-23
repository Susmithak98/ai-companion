# Changelog

## 2.0.0: Production release
- One conversation pipeline shared by the CLI and the new **REST API** (FastAPI, SSE streaming)
- **SQLite** per-user storage replaces JSON/CSV files; `DELETE /v1/users/{id}` for erasure
- LLM client with timeouts, retries/backoff and graceful fallback
- API key auth, per-user rate limiting, input validation, CORS, JSON logging without message text
- Docker image, Docker Compose with Ollama, GitHub Actions CI (lint, tests, image smoke test, GHCR)
- Packaged with `pyproject.toml`: `pip install -e ".[voice]"` and the `aira` command
- 24 tests

## 1.1.0
- Indian-culture agent wired into replies, `--text`/`--mute` modes, lazy Whisper loading,
  configurable paths, crisis response adds Tele MANAS 14416, first test suite

## 1.0.0
- First version: voice loop with Whisper, Ollama phi3:mini, pyttsx3, memory/mood/crisis/wellness agents
