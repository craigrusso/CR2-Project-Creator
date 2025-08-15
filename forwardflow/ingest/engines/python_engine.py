"""Phase 1 Python copy engine with multi-stream and verification (baseline).

Implements a simple per-file copy with optional multi-stream chunking for
files larger than a threshold. Uses xxHash64 for BALANCED verification and
writes a basic MHL via the verify module.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

from ..api.interfaces import Engine, EventSink
from ..api.models import JobSpec, FileSpec, Results
from ..pipeline.verify import hash_file_xxh, write_basic_mhl, parse_mhl
from ..policies.simple_policy import SimplePolicy
from ..logging import get_logger
from ..config import DEFAULTS


@dataclass
class _CopyOutcome:
    src: Path
    dst: Path
    size: int
    ok: bool
    hexdigest: Optional[str] = None
    error: Optional[str] = None


@dataclass
class _JobStats:
    total_bytes: int
    copied_bytes: int
    start_time: float
    last_emit: float
    lock: threading.Lock


@dataclass
class _FileStats:
    file_id: str
    filename: str
    total_bytes: int
    copied_bytes: int
    start_time: float
    last_emit: float
    lock: threading.Lock


class PythonCopyEngine(Engine):
    def __init__(self, sink: Optional[EventSink] = None) -> None:
        self._logger = get_logger("forwardflow.ingest.engine.python")
        self._cancels: dict[str, threading.Event] = {}
        self._pauses: dict[str, threading.Event] = {}
        self._sink = sink
        self._job_stats: dict[str, _JobStats] = {}
        self._file_stats: dict[str, _FileStats] = {}

    def start(self, job: JobSpec) -> None:  # pragma: no cover - used via CLI/UI later
        policy = SimplePolicy()
        files: list[FileSpec] = list(policy.plan(job))
        # Initialize job stats
        total_bytes = sum(f.size_bytes for f in files)
        self._job_stats[job.job_id] = _JobStats(
            total_bytes=total_bytes,
            copied_bytes=0,
            start_time=time.time(),
            last_emit=0.0,
            lock=threading.Lock(),
        )
        self._emit(job.job_id, "job.started", {"total_bytes": total_bytes, "total_files": len(files)})
        results = self._copy_files(job, files)
        # Write MHL only for BALANCED mode
        if (job.options.mode or "BALANCED").upper() == "BALANCED":
            mhl_path = Path(job.destination_root) / f"{job.job_id}.mhl"
            write_basic_mhl(job.job_id, mhl_path, (
                (f.destination, f.size_bytes, o.hexdigest or "")
                for f, o in zip(files, self._outcomes) if o.ok
            ), base_root=Path(job.destination_root))
        elif (job.options.mode or "BALANCED").upper() == "FAST":
            # FAST mode: size check only; warn about missing hashes
            self._logger.warning("FAST mode selected: hashes not computed; integrity not verified")
        stats = self._job_stats.get(job.job_id)
        if stats:
            elapsed = max(1e-3, time.time() - stats.start_time)
            mbps = (stats.copied_bytes / elapsed) / (1024 * 1024)
            self._emit(job.job_id, "job.completed", {
                "bytes": stats.copied_bytes,
                "total": stats.total_bytes,
                "elapsed_s": elapsed,
                "mbps": mbps,
            })

    def pause(self, job_id: str) -> None:  # pragma: no cover - simple flag
        self._pauses.setdefault(job_id, threading.Event()).set()

    def cancel(self, job_id: str) -> None:  # pragma: no cover - simple flag
        self._cancels.setdefault(job_id, threading.Event()).set()

    def _copy_files(self, job: JobSpec, files: Iterable[FileSpec]) -> Results:
        per_file = max(1, job.options.per_file_concurrency or DEFAULTS.per_file_concurrency)
        self._outcomes: list[_CopyOutcome] = []
        results = Results()
        with ThreadPoolExecutor(max_workers=per_file) as pool:
            futures = [pool.submit(self._copy_one, job, f) for f in files]
            for future in as_completed(futures):
                outcome = future.result()
                self._outcomes.append(outcome)
                if outcome.ok:
                    results.files_ok += 1
                    results.bytes_copied += outcome.size
                else:
                    results.files_failed += 1
        return results

    def _copy_one(self, job: JobSpec, spec: FileSpec) -> _CopyOutcome:
        src = spec.source
        dst = spec.destination
        dst_tmp = dst.with_suffix(dst.suffix + ".part")
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Create file ID for tracking
        file_id = f"{job.job_id}_{src.name}"
        filename = src.name
        
        # Initialize file stats
        self._file_stats[file_id] = _FileStats(
            file_id=file_id,
            filename=filename,
            total_bytes=spec.size_bytes,
            copied_bytes=0,
            start_time=time.time(),
            last_emit=0.0,
            lock=threading.Lock(),
        )
        
        # Emit file started event
        self._emit(job.job_id, "file.started", {
            "file_id": file_id,
            "filename": filename,
            "total_bytes": spec.size_bytes,
        })

        # Single-threaded baseline with optional multi-stream
        try:
            # Resume: if final file exists and matches size+hash from existing MHL, skip
            mhl_path = Path(job.destination_root) / f"{job.job_id}.mhl"
            existing = parse_mhl(mhl_path)
            try:
                rel_key = str(dst.relative_to(job.destination_root))
            except Exception:  # noqa: BLE001
                rel_key = str(dst)
            if rel_key in existing:
                expected_size, algo, hexdigest = existing[rel_key]
                if expected_size == spec.size_bytes and hash_file_xxh(src).hexdigest == hexdigest:
                    # Emit file completed event for skipped file
                    self._emit(job.job_id, "file.completed", {
                        "file_id": file_id,
                        "filename": filename,
                        "bytes": spec.size_bytes,
                        "total": spec.size_bytes,
                        "skipped": True,
                    })
                    return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=True, hexdigest=hexdigest)

            # Choose strategy
            streams = max(1, job.options.stream_concurrency or DEFAULTS.stream_concurrency)
            if streams > 1:
                # If a previous partial exists, fall back to single-stream resume
                if dst_tmp.exists() and dst_tmp.stat().st_size < spec.size_bytes:
                    streams = 1
                else:
                    self._copy_multistream(job, src, dst_tmp, spec.size_bytes, streams, file_id)
            else:
                # Resume simple: if .part exists, append from current size
                start_offset = dst_tmp.stat().st_size if dst_tmp.exists() else 0
                mode = "r+b" if dst_tmp.exists() else "wb"
                with src.open("rb") as rf, dst_tmp.open(mode) as wf:
                    if start_offset:
                        rf.seek(start_offset)
                        wf.seek(start_offset)
                    while True:
                        if self._cancels.get(job.job_id, threading.Event()).is_set():
                            # Leave .part file intact
                            self._emit(job.job_id, "file.failed", {
                                "file_id": file_id,
                                "filename": filename,
                                "error": "canceled",
                            })
                            return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error="canceled")
                        if self._pauses.get(job.job_id, threading.Event()).is_set():
                            threading.Event().wait(0.05)
                            continue
                        buf = rf.read(DEFAULTS.io_chunk_size_bytes)
                        if not buf:
                            break
                        wf.write(buf)
                        self._progress(job.job_id, len(buf), file_id)
            # Verify (BALANCED): xxHash64 source vs dest
            src_hash = hash_file_xxh(src)
            dst_hash = hash_file_xxh(dst_tmp)
            if src_hash.hexdigest != dst_hash.hexdigest:
                self._emit(job.job_id, "file.failed", {
                    "file_id": file_id,
                    "filename": filename,
                    "error": "hash_mismatch",
                })
                return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error="hash_mismatch")
            dst_tmp.replace(dst)
            
            # Emit file completed event
            self._emit(job.job_id, "file.completed", {
                "file_id": file_id,
                "filename": filename,
                "bytes": spec.size_bytes,
                "total": spec.size_bytes,
                "skipped": False,
            })
            
            return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=True, hexdigest=src_hash.hexdigest)
        except Exception as exc:  # noqa: BLE001
            self._emit(job.job_id, "file.failed", {
                "file_id": file_id,
                "filename": filename,
                "error": str(exc),
            })
            return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error=str(exc))

    def _copy_multistream(self, job: JobSpec, src: Path, dst_tmp: Path, size_bytes: int, streams: int, file_id: str) -> None:
        # Pre-size destination
        with dst_tmp.open("wb") as wf:
            wf.truncate(size_bytes)

        # Compute ranges
        chunk = size_bytes // streams
        ranges: list[tuple[int, int]] = []
        offset = 0
        for i in range(streams):
            start = offset
            end = start + (chunk if i < streams - 1 else size_bytes - start)
            ranges.append((start, end))
            offset = end

        def worker(r: tuple[int, int]) -> None:
            start, end = r
            with src.open("rb") as rf, dst_tmp.open("r+b") as wf:
                rf.seek(start)
                wf.seek(start)
                remaining = end - start
                while remaining > 0:
                    if self._cancels.get(job.job_id, threading.Event()).is_set():
                        return
                    if self._pauses.get(job.job_id, threading.Event()).is_set():
                        threading.Event().wait(0.05)
                        continue
                    to_read = min(DEFAULTS.io_chunk_size_bytes, remaining)
                    buf = rf.read(to_read)
                    if not buf:
                        break
                    wf.write(buf)
                    remaining -= len(buf)
                    self._progress(job.job_id, len(buf), file_id)

        with ThreadPoolExecutor(max_workers=streams) as execu:
            futs = [execu.submit(worker, r) for r in ranges]
            for f in as_completed(futs):
                f.result()

    def _progress(self, job_id: str, nbytes: int, file_id: Optional[str] = None) -> None:
        # Update job stats
        stats = self._job_stats.get(job_id)
        if stats:
            with stats.lock:
                stats.copied_bytes += nbytes
                now = time.time()
                if now - stats.last_emit < 0.2:
                    pass  # Continue to file stats
                else:
                    stats.last_emit = now
                    elapsed = max(1e-3, now - stats.start_time)
                    mbps = (stats.copied_bytes / elapsed) / (1024 * 1024)
                    remaining = max(0, stats.total_bytes - stats.copied_bytes)
                    eta_s = remaining / (mbps * 1024 * 1024) if mbps > 0 else 0
                    self._emit(job_id, "job.progress", {
                        "bytes": stats.copied_bytes,
                        "total": stats.total_bytes,
                        "mbps": mbps,
                        "eta_seconds": eta_s,
                    })
        
        # Update file stats if provided
        if file_id:
            file_stats = self._file_stats.get(file_id)
            if file_stats:
                with file_stats.lock:
                    file_stats.copied_bytes += nbytes
                    now = time.time()
                    if now - file_stats.last_emit < 0.1:  # More frequent file updates
                        return
                    file_stats.last_emit = now
                    self._emit(job_id, "file.progress", {
                        "file_id": file_id,
                        "filename": file_stats.filename,
                        "bytes": file_stats.copied_bytes,
                        "total": file_stats.total_bytes,
                    })

    def _emit(self, job_id: str, event_type: str, payload: dict) -> None:
        if self._sink:
            try:
                self._sink.emit(event_type, {"job_id": job_id, **payload})
            except Exception as e:
                # Log the error for debugging
                self._logger.error(f"Failed to emit {event_type}: {e}")
                pass


