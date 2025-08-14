"""Metadata extractor protocol and utilities (Phase 1.5)."""

from __future__ import annotations

from typing import Protocol


class MetadataExtractor(Protocol):
    def extract(self, file_path: str) -> dict:
        ...


