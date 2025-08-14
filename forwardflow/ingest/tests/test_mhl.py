from __future__ import annotations

from pathlib import Path

from forwardflow.ingest.pipeline.verify import write_basic_mhl, parse_mhl


def test_write_and_parse_mhl(tmp_path: Path):
    mhl = tmp_path / "job.mhl"
    entries = [
        (tmp_path / "a.mov", 123, "deadbeef"),
        (tmp_path / "b.mov", 456, "beadfeed"),
    ]
    write_basic_mhl("job1", mhl, entries, base_root=tmp_path)
    parsed = parse_mhl(mhl)
    assert parsed["a.mov"] == (123, "xxh64", "deadbeef")
    assert parsed["b.mov"] == (456, "xxh64", "beadfeed")


