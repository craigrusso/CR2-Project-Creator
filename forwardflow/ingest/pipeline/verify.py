"""Verification utilities (Phase 1+).

Phase 0 exposes function stubs and trivial implementations to allow
import-time validation in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple
from datetime import datetime, timezone

import xxhash


@dataclass(frozen=True)
class HashResult:
    algorithm: str
    hexdigest: str


def hash_file_xxh(path: Path, chunk_size: int = 8 * 1024 * 1024) -> HashResult:
    hasher = xxhash.xxh64()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return HashResult(algorithm="xxh64", hexdigest=hasher.hexdigest())


def write_basic_mhl(job_id: str, output_path: Path, entries: Iterable[Tuple[Path, int, str]], base_root: Path | None = None) -> Path:
    lines = ["# Media Hash List (MHL)", f"# job: {job_id}"]
    for path, size_bytes, hexdigest in entries:
        rel = path
        if base_root:
            try:
                rel = path.relative_to(base_root)
            except Exception:  # noqa: BLE001
                rel = path
        lines.append(f"FILE {rel}")
        lines.append(f"  SIZE {size_bytes}")
        lines.append("  ALGO xxh64")
        lines.append(f"  HASH {hexdigest}")
        lines.append(f"  TIMESTAMP {datetime.now(timezone.utc).isoformat()}")
    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def parse_mhl(mhl_path: Path) -> Dict[str, Tuple[int, str, str]]:
    """Return map of rel_path -> (size, algo, hash)."""
    if not mhl_path.exists():
        return {}
    entries: Dict[str, Tuple[int, str, str]] = {}
    cur_path: str | None = None
    size: int | None = None
    algo: str | None = None
    digest: str | None = None
    for raw in mhl_path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("FILE "):
            if cur_path is not None and size is not None and algo and digest:
                entries[cur_path] = (size, algo, digest)
            cur_path = line[5:].strip()
            size = None
            algo = None
            digest = None
        elif line.startswith("SIZE "):
            try:
                size = int(line[5:].strip())
            except ValueError:
                size = None
        elif line.startswith("ALGO "):
            algo = line[5:].strip()
        elif line.startswith("HASH "):
            digest = line[5:].strip()
    if cur_path is not None and size is not None and algo and digest:
        entries[cur_path] = (size, algo, digest)
    return entries


