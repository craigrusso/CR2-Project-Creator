"""Typed models used by the ingest subsystem API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Mapping, Optional


class JobStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    CANCELED = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass(frozen=True)
class FileSpec:
    source: Path
    destination: Path
    size_bytes: int


@dataclass
class Results:
    files_ok: int = 0
    files_failed: int = 0
    bytes_copied: int = 0
    elapsed_seconds: float = 0.0
    mhl_path: Optional[Path] = None
    details: List[Dict] = field(default_factory=list)


@dataclass(frozen=True)
class JobOptions:
    mode: str = "BALANCED"  # map to interfaces.Mode
    per_file_concurrency: int = 2
    stream_concurrency: int = 8
    verify_algorithm: str = "xxh64"
    dest_plan: Optional[Mapping[str, str]] = None


@dataclass
class JobSpec:
    job_id: str
    source_root: Path
    destination_root: Path
    options: JobOptions = field(default_factory=JobOptions)


