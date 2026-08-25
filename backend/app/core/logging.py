from __future__ import annotations

import contextvars
import json
import logging
from datetime import datetime, timezone

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())

    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(request_id)s | "
                "%(name)s | %(message)s"
            )
        )

    root.handlers.clear()
    root.addHandler(handler)
