"""Logging: human-readable locally, JSON lines in production (AIRA_LOG_JSON=true).

Message text is never logged, only metadata, so conversations stay private.
"""
import json
import logging
import sys
from datetime import datetime, timezone

from config import LOG_JSON, LOG_LEVEL


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("user", "emotion", "crisis", "latency_ms", "status", "path"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    plain = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(JsonFormatter() if LOG_JSON else plain)
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(LOG_LEVEL)
