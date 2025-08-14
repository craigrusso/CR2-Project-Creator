from __future__ import annotations

import os
from pathlib import Path

from forwardflow.ingest.api.models import JobOptions, JobSpec
from forwardflow.ingest.engines.python_engine import PythonCopyEngine
from forwardflow.ingest.pipeline.verify import hash_file_xxh
from forwardflow.ingest.policies.simple_policy import SimplePolicy


def _make_large_file(path: Path, size_mb: int = 16) -> None:
    with path.open("wb") as f:
        for _ in range(size_mb):
            f.write(os.urandom(1024 * 1024))


def test_multistream_copy(tmp_path: Path):
    src_root = tmp_path / "src"
    dst_root = tmp_path / "dst"
    src_root.mkdir(); dst_root.mkdir()
    src = src_root / "large.bin"
    _make_large_file(src, size_mb=8)

    job = JobSpec(
        job_id="job-ms",
        source_root=src_root,
        destination_root=dst_root,
        options=JobOptions(per_file_concurrency=1, stream_concurrency=4),
    )
    engine = PythonCopyEngine()
    files = list(SimplePolicy().plan(job))
    res = engine._copy_files(job, files)
    assert (dst_root / "large.bin").exists()
    assert hash_file_xxh(src).hexdigest == hash_file_xxh(dst_root / "large.bin").hexdigest
    assert res.files_ok == 1


def test_resume_from_part(tmp_path: Path):
    src_root = tmp_path / "src"
    dst_root = tmp_path / "dst"
    src_root.mkdir(); dst_root.mkdir()
    src = src_root / "huge.bin"
    _make_large_file(src, size_mb=4)

    job = JobSpec(
        job_id="job-resume",
        source_root=src_root,
        destination_root=dst_root,
        options=JobOptions(per_file_concurrency=1, stream_concurrency=1),
    )
    engine = PythonCopyEngine()
    files = list(SimplePolicy().plan(job))

    # Start copy and cancel early
    engine._cancels[job.job_id] = __import__("threading").Event()
    engine._cancels[job.job_id].set()
    res = engine._copy_files(job, files)
    # .part should exist or nothing copied due to early cancel
    part = (dst_root / "huge.bin").with_suffix(".bin.part")
    # Clear cancel flag and resume
    engine._cancels[job.job_id].clear()
    res2 = engine._copy_files(job, files)
    assert (dst_root / "huge.bin").exists()
    assert hash_file_xxh(src).hexdigest == hash_file_xxh(dst_root / "huge.bin").hexdigest

