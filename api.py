"""Aira REST API: the same companion, served over HTTP for web and mobile apps.

    uvicorn api:app --host 0.0.0.0 --port 8080

Endpoints
    POST   /v1/chat                 one reply as JSON
    POST   /v1/chat/stream          server-sent events (meta, tokens, done)
    GET    /v1/users/{id}/mood      recent mood history
    DELETE /v1/users/{id}           erase everything stored about a user
    GET    /health                  liveness
    GET    /ready                   readiness (is the LLM reachable?)
"""
import json
import logging
import threading
import time
from collections import OrderedDict, defaultdict, deque

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

import agents
import config
import storage
from core.brain import is_ollama_running
from core.pipeline import Session, greeting, respond, respond_stream
from logging_setup import setup_logging

setup_logging()
log = logging.getLogger("aira.api")

app = FastAPI(title="Aira API", version="2.0.0",
              description="Empathetic AI companion: emotion, memory, mood, crisis safety and cultural context.")
if config.CORS_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

USER_ID = r"^[A-Za-z0-9_.-]{1,64}$"


# ---------- auth + rate limiting ----------

def require_api_key(x_api_key: str = Header(default="")) -> None:
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


class RateLimiter:
    """Sliding-window limit per user. In-memory: use Redis or a gateway when running several replicas."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= self.per_minute:
                raise HTTPException(status_code=429, detail="Too many messages, please slow down")
            q.append(now)


limiter = RateLimiter(config.RATE_LIMIT_PER_MINUTE)


class SessionStore:
    """Keeps recent conversation context per user (bounded LRU). Long-term memory lives in SQLite."""

    def __init__(self, max_sessions: int = 1000):
        self.max = max_sessions
        self.sessions: OrderedDict[str, Session] = OrderedDict()
        self.lock = threading.Lock()

    def get(self, user_id: str) -> Session:
        with self.lock:
            session = self.sessions.pop(user_id, None) or Session(user_id=user_id)
            self.sessions[user_id] = session
            while len(self.sessions) > self.max:
                self.sessions.popitem(last=False)
            return session

    def drop(self, user_id: str) -> None:
        with self.lock:
            self.sessions.pop(user_id, None)


sessions = SessionStore()


# ---------- schemas ----------

class ChatRequest(BaseModel):
    user_id: str = Field(..., pattern=USER_ID, examples=["priya-123"])
    message: str = Field(..., min_length=1, max_length=config.MAX_MESSAGE_CHARS,
                         examples=["I miss home so much today"])


class ChatResponse(BaseModel):
    reply: str
    emotion: str
    crisis_level: str
    culture: str | None = None
    exercise: dict | None = None
    low_mood_note: str | None = None
    ended: bool = False


# ---------- middleware ----------

@app.middleware("http")
async def access_log(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    log.info("request", extra={"path": request.url.path, "status": response.status_code,
                               "latency_ms": round((time.perf_counter() - started) * 1000)})
    return response


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


# ---------- routes ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not is_ollama_running():
        raise HTTPException(status_code=503, detail="LLM not reachable")
    return {"status": "ready", "model": config.OLLAMA_MODEL}


@app.get("/v1/users/{user_id}/greeting", dependencies=[Depends(require_api_key)])
def get_greeting(user_id: str):
    _validate_user(user_id)
    return {"reply": greeting(user_id)}


@app.post("/v1/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
def chat(body: ChatRequest):
    limiter.check(body.user_id)
    return respond(sessions.get(body.user_id), body.message).to_dict()


@app.post("/v1/chat/stream", dependencies=[Depends(require_api_key)])
def chat_stream(body: ChatRequest):
    limiter.check(body.user_id)
    session = sessions.get(body.user_id)

    def events():
        for event in respond_stream(session, body.message):
            yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/v1/users/{user_id}/mood", dependencies=[Depends(require_api_key)])
def mood(user_id: str, limit: int = 10):
    _validate_user(user_id)
    return {"summary": agents.get_mood_summary(user_id),
            "history": storage.recent_moods(user_id, max(1, min(limit, 100)))}


@app.delete("/v1/users/{user_id}", dependencies=[Depends(require_api_key)])
def delete_user(user_id: str):
    _validate_user(user_id)
    sessions.drop(user_id)
    return {"deleted_records": storage.delete_user(user_id)}


def _validate_user(user_id: str) -> None:
    import re
    if not re.match(USER_ID, user_id):
        raise HTTPException(status_code=422, detail="Invalid user_id")
