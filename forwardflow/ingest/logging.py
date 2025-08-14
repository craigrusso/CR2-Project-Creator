"""Structured logging helpers for ingest subsystem.

Avoids coupling to the app's global logging; provides a minimal
JSON-capable logger for internal events.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Dict


def get_logger(name: str = "forwardflow.ingest") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def to_json(obj: Any) -> str:
    if is_dataclass(obj):
        return json.dumps(asdict(obj), sort_keys=True)
    if isinstance(obj, (dict, list, tuple)):
        return json.dumps(obj, sort_keys=True)
    return json.dumps(obj)


