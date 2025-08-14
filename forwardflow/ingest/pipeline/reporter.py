"""Human and JSON reporters (Phase 1)."""

from __future__ import annotations

from pathlib import Path

from ..logging import get_logger


class ReporterImpl:
    def __init__(self, job_id: str, logs_dir: Path) -> None:
        self.job_id = job_id
        self.logs_dir = logs_dir
        self._logger = get_logger(f"forwardflow.ingest.job.{job_id}")

    def info(self, message: str, **fields) -> None:  # pragma: no cover - stub
        self._logger.info(message + (f" | {fields}" if fields else ""))

    def warn(self, message: str, **fields) -> None:  # pragma: no cover - stub
        self._logger.warning(message + (f" | {fields}" if fields else ""))

    def error(self, message: str, **fields) -> None:  # pragma: no cover - stub
        self._logger.error(message + (f" | {fields}" if fields else ""))

    def path_for_job_log(self, job_id: str) -> str:  # pragma: no cover - stub
        path = self.logs_dir / f"{job_id}.log"
        return str(path)


