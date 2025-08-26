"""View-model for Ingest UI (framework-agnostic).

Phase 0 exposes a minimal class to allow import.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Import engines - only import when actually needed to avoid double registration
CPP_ENGINE_AVAILABLE = True  # We'll import when needed


@dataclass
class IngestViewModel:
    enabled: bool = True # Changed to True as FF_INGEST_ENABLED is removed
    source: Optional[Path] = None
    destination: Optional[Path] = None
    mode: str = "BALANCED"  # FAST | BALANCED | STRICT(disabled)
    per_file_concurrency: int = 2
    stream_concurrency: int = 8
    _engine_override: Optional[EnhancedHighPerfTransferEngine] = None

    def start(self, job_id: str) -> None:  # pragma: no cover - UI wireup later
        if not self.enabled:
            return
        if not self.source or not self.destination:
            return
        
        # Import engine only when needed to avoid double registration
        try:
            from ..engines.High_perf.enhanced_high_perf_engine import EnhancedHighPerfTransferEngine, CopyJob
        except Exception as e:
            print(f"DEBUG: Failed to import C++ engine in ingest_vm: {e}")
            return
            
        # Use the engine override (with event sink) if provided, otherwise create default
        engine = self._engine_override or EnhancedHighPerfTransferEngine()
        # Track current job for pause/cancel wiring
        self._current_job_id = job_id
        self._current_engine = engine
        # Create a CopyJob object for the C++ engine
        copy_job = CopyJob()
        copy_job.source_paths = [str(self.source)]
        copy_job.destination_paths = [str(self.destination)]
        copy_job.job_id = job_id
        copy_job.files_in_flight = self.per_file_concurrency
        copy_job.ranges_per_file = self.stream_concurrency
        engine.copy_files(copy_job)

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


