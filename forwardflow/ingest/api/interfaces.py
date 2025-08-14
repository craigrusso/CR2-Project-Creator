"""Public API interfaces for the ingest subsystem.

These are simple Protocols / base classes to define contracts
without introducing heavy dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Optional, Protocol, runtime_checkable


class Mode(Enum):
    FAST = auto()
    BALANCED = auto()
    STRICT = auto()


class Backend(Enum):
    AUTO = auto()
    PYTHON = auto()
    NATIVE = auto()
    OS_TOOL = auto()


@runtime_checkable
class EventSink(Protocol):
    def emit(self, event_type: str, payload: dict) -> None:
        ...


@runtime_checkable
class Reporter(Protocol):
    def info(self, message: str, **fields) -> None: ...
    def warn(self, message: str, **fields) -> None: ...
    def error(self, message: str, **fields) -> None: ...
    def path_for_job_log(self, job_id: str) -> str: ...


@runtime_checkable
class MetadataExtractor(Protocol):
    def extract(self, file_path: str) -> dict:
        ...


@runtime_checkable
class Engine(Protocol):
    def start(self, job: "JobSpec") -> None: ...
    def pause(self, job_id: str) -> None: ...
    def cancel(self, job_id: str) -> None: ...


@runtime_checkable
class Policy(Protocol):
    def plan(self, job: "JobSpec") -> Iterable["FileSpec"]:
        ...


@runtime_checkable
class Pipeline(Protocol):
    def submit(self, job: "JobSpec") -> None: ...


@dataclass(frozen=True)
class UiBindings:
    # Stubs for VM wiring; UI should bind to these in Phase 1
    can_start: bool = False
    can_pause: bool = False
    can_cancel: bool = False


