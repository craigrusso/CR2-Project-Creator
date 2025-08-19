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
        
        # Handle both single and multi-destination cases
        if job.destination_roots and len(job.destination_roots) > 0:
            # Use the first destination for planning (multi-destination will be handled by engine)
            dst_root = Path(job.destination_roots[0])
        elif job.destination_root:
            # Legacy single destination
            dst_root = Path(job.destination_root)
        else:
            raise ValueError("No destination root provided in job specification")
        
        for path in src_root.rglob("*"):
            if path.is_file():
                rel = path.relative_to(src_root)
                dst = dst_root / rel
                size = path.stat().st_size
                yield FileSpec(source=path, destination=dst, size_bytes=size)


