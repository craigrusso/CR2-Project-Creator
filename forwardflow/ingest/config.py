"""Ingest configuration and feature flags.

All flags default to a safe, internal state. The primary gating flag
`FF_INGEST_ENABLED` must be set to True to expose any UI or CLI
surfaces beyond internal testing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


# Primary feature flag for exposing ingest functionality publicly
# Check environment variable first, then default to True
FF_INGEST_ENABLED: bool = os.environ.get('FF_INGEST_ENABLED', 'True').lower() == 'true'


@dataclass(frozen=True)
class IngestDefaults:
    # Phase 1 defaults (kept here for centralized configuration)
    # Presets for common link speeds
    # Users shouldn't need to tweak in most cases; UI can set based on chosen preset
    per_file_concurrency: int = 4  # Increased from 2
    stream_concurrency: int = 16   # Increased from 8
    min_multistream_size_bytes: int = 100 * 1024 * 1024  # Reduced to 100 MiB for more files
    io_chunk_size_bytes: int = 256 * 1024 * 1024  # Increased to 128 MiB for much better performance
    verify_algorithm: str = "xxh64"  # Phase 1: non-cryptographic


DEFAULTS = IngestDefaults()


