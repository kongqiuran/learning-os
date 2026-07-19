import json
import logging
import os
import sys
from datetime import datetime, timezone


CONTEXT_FIELDS = (
    "event",
    "request_id",
    "method",
    "path",
    "user_id",
    "task_id",
    "document_id",
    "course_id",
    "package_id",
    "scene",
    "status",
    "stage",
    "duration_ms",
    "attempt",
)


class JsonLogFormatter(logging.Formatter):
    """Render application logs as one JSON object per line."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in CONTEXT_FIELDS:
            payload[field] = getattr(record, field, None)

        explicit_exception = getattr(record, "exception", None)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        elif explicit_exception is not None:
            payload["exception"] = str(explicit_exception)
        else:
            payload["exception"] = None
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level=None):
    """Configure a single stdout handler without adding external dependencies."""

    root = logging.getLogger()
    selected_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    root.setLevel(getattr(logging, selected_level, logging.INFO))
    if any(getattr(handler, "learning_os_handler", False) for handler in root.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.learning_os_handler = True
    handler.setFormatter(JsonLogFormatter())
    root.addHandler(handler)


def get_logger(name):
    return logging.getLogger(name)
