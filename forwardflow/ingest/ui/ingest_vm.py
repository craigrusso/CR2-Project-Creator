"""View-model for Ingest UI (framework-agnostic).

Phase 0 exposes a minimal class to allow import.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..api.models import JobOptions, JobSpec
from ..engines.python_engine import PythonCopyEngine
from ..config import FF_INGEST_ENABLED


@dataclass
class IngestViewModel:
    enabled: bool = FF_INGEST_ENABLED
    source: Optional[Path] = None
    destination: Optional[Path] = None
    mode: str = "BALANCED"  # FAST | BALANCED | STRICT(disabled)
    per_file_concurrency: int = 2
    stream_concurrency: int = 8

    def start(self, job_id: str) -> None:  # pragma: no cover - UI wireup later
        if not self.enabled:
            return
        if not self.source or not self.destination:
            return
        opts = JobOptions(
            mode=self.mode,
            per_file_concurrency=self.per_file_concurrency,
            stream_concurrency=self.stream_concurrency,
        )
        job = JobSpec(
            job_id=job_id,
            source_root=self.source,
            destination_root=self.destination,
            options=opts,
        )
        engine = getattr(self, "_engine_override", None) or PythonCopyEngine()
        # Track current job for pause/cancel wiring
        self._current_job_id = job_id
        self._current_engine = engine
        engine.start(job)

    def pause_current(self) -> None:  # pragma: no cover - UI wireup later
        job_id = getattr(self, "_current_job_id", None)
        engine = getattr(self, "_current_engine", None)
        if job_id and engine:
            try:
                engine.pause(job_id)
            except Exception:
                pass

    def cancel_current(self) -> None:  # pragma: no cover - UI wireup later
        job_id = getattr(self, "_current_job_id", None)
        engine = getattr(self, "_current_engine", None)
        if job_id and engine:
            try:
                engine.cancel(job_id)
            except Exception:
                pass


