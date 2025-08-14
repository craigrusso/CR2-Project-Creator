"""Turbo Ingest package.

Phase 0: Scaffold & Guardrails
- Self-contained package; does not import or modify existing app code
- Feature-flag gated via `config.FF_INGEST_ENABLED`
"""

from .config import FF_INGEST_ENABLED

__all__ = [
    "FF_INGEST_ENABLED",
]


