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
    # NEW: Multi-destination support
    verify_mode: str = "FAST"  # FAST, STREAM_VERIFY, READBACK_VERIFY
    preset: str = "auto"  # auto, usb, network, custom
    # NEW: Verification report generation
    generate_verification_report: bool = True
    # NEW: Cloud source detection
    cloud_source: bool = False
    # NEW: BLAST cache drive selection (optional)
    blast_cache_drive: Optional[str] = None


@dataclass
class JobSpec:
    job_id: str
    source_root: Path
    destination_root: Optional[Path] = None  # Legacy single destination
    # NEW: Multiple destinations support
    destination_roots: Optional[List[Path]] = None
    options: JobOptions = field(default_factory=JobOptions)
    
    def __post_init__(self):
        # Ensure we have at least one destination
        if self.destination_roots is None:
            if self.destination_root is not None:
                self.destination_roots = [self.destination_root]
            else:
                raise ValueError("Either destination_root or destination_roots must be provided")


