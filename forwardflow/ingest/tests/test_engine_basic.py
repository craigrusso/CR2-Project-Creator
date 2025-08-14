from __future__ import annotations

import os
from pathlib import Path

from forwardflow.ingest.api.models import JobSpec, JobOptions
from forwardflow.ingest.engines.python_engine import PythonCopyEngine
from forwardflow.ingest.pipeline.verify import hash_file_xxh


def test_engine_copies_and_verifies(tmp_path: Path):
    src_root = tmp_path / "src"
    dst_root = tmp_path / "dst"
    src_root.mkdir()
    dst_root.mkdir()

    data = b"a" * (2 * 1024 * 1024) + b"b" * (2 * 1024 * 1024)
    (src_root / "clip.mov").write_bytes(data)

    job = JobSpec(
        job_id="job1",
        source_root=src_root,
        destination_root=dst_root,
        options=JobOptions(per_file_concurrency=1, stream_concurrency=1),
    )

    engine = PythonCopyEngine()
    from forwardflow.ingest.policies.simple_policy import SimplePolicy
    files = list(SimplePolicy().plan(job))
    res = engine._copy_files(job, files)

    assert (dst_root / "clip.mov").exists()
    assert hash_file_xxh(src_root / "clip.mov").hexdigest == hash_file_xxh(dst_root / "clip.mov").hexdigest
    assert res.files_ok == 1


