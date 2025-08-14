"""Placeholder for optional native helper backends (Phase 6)."""

from __future__ import annotations

from ..api.interfaces import Engine
from ..api.models import JobSpec


class NativeEngine(Engine):
    def start(self, job: JobSpec) -> None:  # pragma: no cover - stub
        return None

    def pause(self, job_id: str) -> None:  # pragma: no cover - stub
        return None

    def cancel(self, job_id: str) -> None:  # pragma: no cover - stub
        return None


