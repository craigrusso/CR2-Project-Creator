from __future__ import annotations

from pathlib import Path

from forwardflow.ingest.ui.ingest_vm import IngestViewModel
from forwardflow.ingest.api.models import JobSpec, JobOptions
from forwardflow.ingest.engines.python_engine import PythonCopyEngine
from forwardflow.ingest.policies.simple_policy import SimplePolicy


def test_vm_start_balanced(tmp_path: Path):
    src_root = tmp_path / "src"; dst_root = tmp_path / "dst"
    src_root.mkdir(); dst_root.mkdir()
    (src_root / "a.txt").write_text("hello")

    vm = IngestViewModel()
    vm.source = src_root
    vm.destination = dst_root
    vm.mode = "BALANCED"
    vm.per_file_concurrency = 1
    vm.stream_concurrency = 1

    vm.start("jobvm")
    assert (dst_root / "a.txt").exists()
    assert (dst_root / "jobvm.mhl").exists()


def test_fast_mode_skips_mhl(tmp_path: Path):
    src_root = tmp_path / "src"; dst_root = tmp_path / "dst"
    src_root.mkdir(); dst_root.mkdir()
    (src_root / "b.txt").write_text("world")

    job = JobSpec(
        job_id="jobfast",
        source_root=src_root,
        destination_root=dst_root,
        options=JobOptions(mode="FAST", per_file_concurrency=1, stream_concurrency=1),
    )
    PythonCopyEngine().start(job)
    assert (dst_root / "b.txt").exists()
    assert not (dst_root / "jobfast.mhl").exists()


