"""Adaptive scheduler placeholder (Phase 3)."""

from __future__ import annotations

from ..api.interfaces import Pipeline
from ..api.models import JobSpec


class Scheduler(Pipeline):
    def submit(self, job: JobSpec) -> None:  # pragma: no cover - stub
        return None


