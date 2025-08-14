"""Destination and network probe stubs (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeResult:
    write_mbps: float
    latency_ms: float


def probe_destination(path: str) -> ProbeResult:  # pragma: no cover - stub
    return ProbeResult(write_mbps=0.0, latency_ms=0.0)


