"""Typed event schemas for ingest lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Dict


@dataclass(frozen=True)
class Event:
    job_id: str
    payload: Dict


@dataclass(frozen=True)
class JobStarted(Event):
    type: ClassVar[str] = "job.started"


@dataclass(frozen=True)
class JobProgress(Event):
    type: ClassVar[str] = "job.progress"


@dataclass(frozen=True)
class JobCompleted(Event):
    type: ClassVar[str] = "job.completed"


@dataclass(frozen=True)
class JobFailed(Event):
    type: ClassVar[str] = "job.failed"


