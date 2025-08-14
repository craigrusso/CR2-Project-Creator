"""Default planning policy stub.

Plans a 1:1 source→destination mapping under provided roots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator

from ..api.interfaces import Policy
from ..api.models import FileSpec, JobSpec


class SimplePolicy(Policy):
    def plan(self, job: JobSpec) -> Iterable[FileSpec]:
        src_root = Path(job.source_root)
        dst_root = Path(job.destination_root)
        for path in src_root.rglob("*"):
            if path.is_file():
                rel = path.relative_to(src_root)
                dst = dst_root / rel
                size = path.stat().st_size
                yield FileSpec(source=path, destination=dst, size_bytes=size)


