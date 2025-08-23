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
from datetime import datetime

from ..api.interfaces import Engine, EventSink
from ..api.models import JobSpec, FileSpec, Results
from ..pipeline.verify import hash_file_xxh, write_basic_mhl, parse_mhl
from ..pipeline.verification_report import VerificationReportManager, VerificationRecord
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
    last_emit_bytes: int = 0 # Added for performance monitoring


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
        # NEW: Verification report managers for each destination
        self._report_managers: dict[str, VerificationReportManager] = {}
        self._cpp_engine_used = False # Flag to track if C++ engine was used
        self._cpp_engine: Optional[any] = None # Reference to the C++ engine for cancellation

    def start(self, job: JobSpec) -> None:  # pragma: no cover - used via CLI/UI later
        print(f"DEBUG: PythonCopyEngine.start called with job: {job.job_id}")
        try:
            # Handle multiple destinations
            if hasattr(job, 'destination_roots') and job.destination_roots:
                print(f"DEBUG: Job has destination_roots: {job.destination_roots}")
                # Multi-destination fan-out (even for single destination in destination_roots)
                self._start_multi_destination(job)
            else:
                print(f"DEBUG: Job has single destination: {job.destination_root}")
                # Single destination (legacy)
                self._start_single_destination(job)
        except Exception as e:
            print(f"DEBUG: Error in PythonCopyEngine.start: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _start_single_destination(self, job: JobSpec) -> None:
        """Start a single-destination copy job"""
        print(f"DEBUG: _start_single_destination called with job: {job.job_id}")
        try:
            # Convert single destination to multi-destination format for C++ engine
            if not hasattr(job, 'destination_roots'):
                job.destination_roots = [job.destination_root]
            
            # Use the multi-destination C++ engine
            self._start_multi_destination(job)
            
        except Exception as e:
            print(f"DEBUG: Error in _start_single_destination: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _start_multi_destination(self, job: JobSpec) -> None:
        """Start a multi-destination fan-out copy job"""
        print(f"DEBUG: _start_multi_destination called with job: {job.job_id}")
        try:
            # Import and use ONLY the C++ engine - no fallbacks
            print(f"DEBUG: Attempting to import C++ engine...")
            
            # Use the working setuptools-built engine from High_perf directory
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Add the High_perf directory to the path
            high_perf_path = os.path.join(current_dir, "High_perf")
            if high_perf_path not in sys.path:
                sys.path.insert(0, high_perf_path)
                print(f"DEBUG: Added High_perf path: {high_perf_path}")
            
            # Import C++ engine - this MUST succeed
            import enhanced_high_perf_engine
            cpp_engine = enhanced_high_perf_engine
            print(f"DEBUG: C++ engine imported successfully from High_perf directory")
            
            print("DEBUG: C++ engine found, using it for maximum performance")
            self._cpp_engine_used = True
            self._start_multi_destination_cpp(job, cpp_engine)
            
        except Exception as e:
            print(f"DEBUG: C++ engine failed: {e}")
            print("ERROR: C++ engine is required and failed to import. Cannot proceed with file copy operation.")
            raise RuntimeError(f"C++ engine import failed: {e}")
    
    def _start_multi_destination_cpp(self, job: JobSpec, cpp_engine) -> None:
        """Use C++ engine for multi-destination fan-out"""
        print(f"DEBUG: _start_multi_destination_cpp called with job: {job.job_id}")
        try:
            print(f"DEBUG: Creating C++ CopyJob...")
            # Create C++ CopyJob
            cpp_job = cpp_engine.CopyJob()
            cpp_job.source_paths = [str(job.source_root)]
            cpp_job.destination_paths = [str(dest) for dest in job.destination_roots]
            cpp_job.preset = job.options.preset
            cpp_job.verify_mode = job.options.verify_mode
            cpp_job.adaptive_parameters = True
            # NEW: Set verification report options
            cpp_job.generate_verification_report = job.options.generate_verification_report
            cpp_job.job_id = job.job_id
            print(f"DEBUG: C++ CopyJob created successfully")
            
            print(f"DEBUG: Setting up event sink...")
            # Set up event sink - use ONLY set_event_sink, not progress_callback
            def event_sink(event_type: str, payload: dict):
                try:
                    print(f"DEBUG: C++ engine emitted event: {event_type}")
                    
                    # Handle events without payloads from C++ engine
                    if event_type == "file.started":
                        # Track file progress - increment copied files count
                        if job.job_id in self._job_stats:
                            with self._job_stats[job.job_id].lock:
                                # Update progress based on files completed
                                files_completed = getattr(self._job_stats[job.job_id], 'files_completed', 0)
                                files_completed += 1
                                self._job_stats[job.job_id].files_completed = files_completed
                                
                                # Calculate progress percentage
                                total_files = len(files)
                                progress_percent = (files_completed / total_files) * 100 if total_files > 0 else 0
                                
                                # Emit progress update immediately
                                self._emit(job.job_id, "job.progress", {
                                    "bytes_copied": self._job_stats[job.job_id].copied_bytes,
                                    "total_bytes": total_bytes,
                                    "progress_percent": progress_percent,
                                    "files_completed": files_completed,
                                    "total_files": total_files,
                                    "speed_mbps": 0,
                                    "elapsed_time": time.time() - self._job_stats[job.job_id].start_time
                                })
                                
                                # Emit file started event with actual filename
                                filename = f"File {files_completed}" if files_completed <= len(files) else "Copying..."
                                self._emit(job.job_id, "file.started", {
                                    "file_id": f"file_{files_completed}",
                                    "filename": filename,
                                    "total_bytes": 0,
                                })
                                
                    elif event_type == "file.completed":
                        # Track file completion
                        if job.job_id in self._job_stats:
                            with self._job_stats[job.job_id].lock:
                                # Update copied bytes (estimate based on average file size)
                                files_completed = getattr(self._job_stats[job.job_id], 'files_completed', 0)
                                avg_file_size = total_bytes / len(files) if len(files) > 0 else 0
                                self._job_stats[job.job_id].copied_bytes = int(files_completed * avg_file_size)
                                
                                # Emit file completed event
                                filename = f"File {files_completed}" if files_completed <= len(files) else "Completed"
                                self._emit(job.job_id, "file.completed", {
                                    "file_id": f"file_{files_completed}",
                                    "filename": filename,
                                    "bytes": int(avg_file_size),
                                    "total": int(avg_file_size),
                                    "skipped": False,
                                })
                                
                    elif event_type == "job.progress":
                        # Update job progress based on files completed
                        if job.job_id in self._job_stats:
                            with self._job_stats[job.job_id].lock:
                                files_completed = getattr(self._job_stats[job.job_id], 'files_completed', 0)
                                total_files = len(files)
                                progress_percent = (files_completed / total_files) * 100 if total_files > 0 else 0
                                
                                # Estimate copied bytes
                                avg_file_size = total_bytes / total_files if total_files > 0 else 0
                                copied_bytes = int(files_completed * avg_file_size)
                                self._job_stats[job.job_id].copied_bytes = copied_bytes
                                
                                # Calculate speed
                                elapsed = time.time() - self._job_stats[job.job_id].start_time
                                speed_mbps = (copied_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                                
                                # Emit progress update
                                self._emit(job.job_id, "job.progress", {
                                    "bytes_copied": copied_bytes,
                                    "total_bytes": total_bytes,
                                    "progress_percent": progress_percent,
                                    "files_completed": files_completed,
                                    "total_files": total_files,
                                    "speed_mbps": speed_mbps,
                                    "elapsed_time": elapsed
                                })
                                
                    else:
                        # For other events, just log them
                        print(f"DEBUG: Unhandled C++ event: {event_type}")
                        
                except Exception as e:
                    print(f"ERROR: Exception in event sink: {e}")
                    import traceback
                    traceback.print_exc()
            
            # DO NOT set progress_callback - it conflicts with set_event_sink
            # cpp_job.progress_callback = event_sink  # REMOVED
            
            print(f"DEBUG: Event sink set up successfully")
            
            print(f"DEBUG: Creating C++ engine...")
            # Create engine and run
            engine = cpp_engine.EnhancedHighPerfTransferEngine()
            engine.set_event_sink(event_sink)
            # Store reference to C++ engine for cancellation
            self._cpp_engine = engine
            print(f"DEBUG: C++ engine created successfully")
            
            print(f"DEBUG: Initializing job stats...")
            # Initialize job stats - use policy to get file list instead of recursive scan
            policy = SimplePolicy()
            files: list[FileSpec] = list(policy.plan(job))
            total_bytes = sum(f.size_bytes for f in files)
            self._job_stats[job.job_id] = _JobStats(
                total_bytes=total_bytes,
                copied_bytes=0,
                start_time=time.time(),
                last_emit=0.0,
                lock=threading.Lock(),
            )
            # Initialize files completed counter
            self._job_stats[job.job_id].files_completed = 0
            print(f"DEBUG: Job stats initialized: total_bytes={total_bytes}, total_files={len(files)}")
            
            print(f"DEBUG: Emitting job.started event...")
            self._emit(job.job_id, "job.started", {"total_bytes": total_bytes, "total_files": len(files)})
            print(f"DEBUG: job.started event emitted successfully")
            
            print(f"DEBUG: About to call engine.copy_files...")
            # Run the copy
            stats = engine.copy_files(cpp_job)
            print(f"DEBUG: engine.copy_files completed successfully")
            
            print(f"DEBUG: Emitting job.completed event...")
            # Emit completion
            elapsed = max(1e-3, time.time() - self._job_stats[job.job_id].start_time)
            self._emit(job.job_id, "job.completed", {
                "bytes": stats.copied_bytes,
                "total": stats.total_bytes,
                "elapsed": elapsed,
                "speed": stats.copied_bytes / elapsed if elapsed > 0 else 0,
            })
            print(f"DEBUG: job.completed event emitted successfully")
            print(f"DEBUG: _start_multi_destination_cpp completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in _start_multi_destination_cpp: {e}")
            import traceback
            traceback.print_exc()
            raise

    def pause(self, job_id: str) -> None:  # pragma: no cover - simple flag
        self._pauses.setdefault(job_id, threading.Event()).set()

    def resume(self, job_id: str) -> None:  # pragma: no cover - clear pause flag
        if job_id in self._pauses:
            self._pauses[job_id].clear()

    def get_current_job_id(self) -> Optional[str]:
        """Get the current job ID if any job is running"""
        return next(iter(self._job_stats.keys()), None) if self._job_stats else None
    
    def _ensure_report_manager(self, job: JobSpec) -> None:
        """Ensure verification report manager exists for the job destination."""
        if not job.options.generate_verification_report:
            return
            
        # For single destination jobs
        if hasattr(job, 'destination_root') and job.destination_root:
            dest_key = str(job.destination_root)
            if dest_key not in self._report_managers:
                self._report_managers[dest_key] = VerificationReportManager(job.destination_root)
                # Start the job report
                self._report_managers[dest_key].start_job_report(
                    job.job_id, 
                    datetime.fromtimestamp(self._job_stats[job.job_id].start_time)
                )
        
        # For multi-destination jobs
        elif hasattr(job, 'destination_roots') and job.destination_roots:
            for dest_root in job.destination_roots:
                dest_key = str(dest_root)
                if dest_key not in self._report_managers:
                    self._report_managers[dest_key] = VerificationReportManager(dest_root)
                    # Start the job report
                    self._report_managers[dest_key].start_job_report(
                        job.job_id, 
                        datetime.fromtimestamp(self._job_stats[job.job_id].start_time)
                    )
    
    def _finalize_verification_reports(self, job: JobSpec) -> None:
        """Finalize verification reports for all destinations."""
        if not job.options.generate_verification_report:
            return
            
        try:
            # For single destination jobs
            if hasattr(job, 'destination_root') and job.destination_root:
                dest_key = str(job.destination_root)
                if dest_key in self._report_managers:
                    self._report_managers[dest_key].finalize_job_report(job.job_id)
                    print(f"DEBUG: Finalized verification report for destination: {dest_key}")
            
            # For multi-destination jobs
            elif hasattr(job, 'destination_roots') and job.destination_roots:
                for dest_root in job.destination_roots:
                    dest_key = str(dest_root)
                    if dest_key in self._report_managers:
                        self._report_managers[dest_key].finalize_job_report(job.job_id)
                        print(f"DEBUG: Finalized verification report for destination: {dest_key}")
                        
        except Exception as e:
            self._logger.error(f"Failed to finalize verification reports: {e}")
            # Don't fail the transfer job due to report generation issues

    def _add_verification_record(self, job: JobSpec, spec: FileSpec, 
                                src_hash, dst_hash, status: str, error_message: Optional[str] = None) -> None:
        """Add a verification record to the appropriate report manager."""
        if not job.options.generate_verification_report:
            return
            
        try:
            # Determine destination key for report manager
            dest_key = None
            if hasattr(job, 'destination_root') and job.destination_root:
                dest_key = str(job.destination_root)
            elif hasattr(job, 'destination_roots') and job.destination_roots:
                # For multi-destination, use the first one (or we could track which one this file went to)
                dest_key = str(job.destination_roots[0])
            
            if dest_key and dest_key in self._report_managers:
                # Create verification record
                record = VerificationRecord(
                    filename=spec.source.name,
                    source_path=str(spec.source),
                    destination_path=str(spec.destination),
                    file_size_bytes=spec.size_bytes,
                    hash_type=job.options.verify_algorithm if src_hash else "NONE",
                    source_hash=src_hash.hexdigest if src_hash else None,
                    destination_hash=dst_hash.hexdigest if dst_hash else None,
                    status=status,
                    timestamp=datetime.now(),
                    error_message=error_message
                )
                
                # Add to report manager
                self._report_managers[dest_key].add_verification_record(job.job_id, record)
                
        except Exception as e:
            self._logger.error(f"Failed to add verification record: {e}")
            # Don't fail the transfer job due to report generation issues

    def cancel(self, job_id: str) -> None:  # pragma: no cover - simple flag
        """Cancel a job immediately and forcefully."""
        print(f"DEBUG: Canceling job {job_id}")
        # Set the cancel event
        self._cancels.setdefault(job_id, threading.Event()).set()
        
        # Force stop any running copy operations
        if self._cpp_engine:
            try:
                print(f"DEBUG: Shutting down C++ engine for job {job_id}")
                self._cpp_engine.cancel()
                print(f"DEBUG: C++ engine shutdown for job {job_id}")
            except Exception as e:
                print(f"DEBUG: Error shutting down C++ engine: {e}")
        
        print(f"DEBUG: Job {job_id} cancellation complete")

    def cancel_destination(self, dest_path: str) -> None:
        """Cancel a specific destination by path"""
        print(f"DEBUG: cancel_destination called for: {dest_path}")
        # Find all job IDs that contain this destination path
        for job_id in list(self._job_stats.keys()):
            if dest_path in job_id:
                print(f"DEBUG: Canceling job {job_id} for destination {dest_path}")
                self.cancel(job_id)

    def _copy_files(self, job: JobSpec, files: list[FileSpec]) -> None:
        """Copy files according to the plan"""
        print(f"DEBUG: _copy_files called with {len(files)} files")
        try:
            print(f"DEBUG: Initializing job stats...")
            # Initialize job stats
            total_bytes = sum(f.size_bytes for f in files)
            self._job_stats[job.job_id] = _JobStats(
                total_bytes=total_bytes,
                copied_bytes=0,
                start_time=time.time(),
                last_emit=0.0,
                lock=threading.Lock(),
            )
            print(f"DEBUG: Job stats initialized: total_bytes={total_bytes}")
            
            print(f"DEBUG: Emitting job.started event...")
            self._emit(job.job_id, "job.started", {"total_bytes": total_bytes, "total_files": len(files)})
            print(f"DEBUG: job.started event emitted")
            
            print(f"DEBUG: Starting file copying...")
            results = self._copy_files_impl(job, files)
            print(f"DEBUG: File copying completed")
            
            # Emit job completion event
            elapsed = max(1e-3, time.time() - self._job_stats[job.job_id].start_time)
            self._emit(job.job_id, "job.completed", {
                "bytes": results.bytes_copied,
                "total": self._job_stats[job.job_id].total_bytes,
                "elapsed": elapsed,
                "speed": results.bytes_copied / elapsed if elapsed > 0 else 0,
            })
            print(f"DEBUG: job.completed event emitted")
            
            # Finalize verification reports if enabled
            if job.options.generate_verification_report:
                self._finalize_verification_reports(job)
            
        except Exception as e:
            print(f"DEBUG: Error in _copy_files: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _copy_files_impl(self, job: JobSpec, files: list[FileSpec]) -> Results:
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
        
        # Add safety checks
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._logger.error(f"Failed to create destination directory: {e}")
            return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error=f"Failed to create directory: {e}")

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
        
        # NEW: Initialize verification report manager if enabled
        if job.options.generate_verification_report:
            self._ensure_report_manager(job)
        
        # Emit file started event
        self._emit(job.job_id, "file.started", {
            "file_id": file_id,
            "filename": filename,
            "total_bytes": spec.size_bytes,
        })

        # Single-threaded baseline with optional multi-stream
        try:
            # Add safety check for source file
            if not src.exists():
                error_msg = f"Source file does not exist: {src}"
                self._logger.error(error_msg)
                self._emit(job.job_id, "file.failed", {
                    "file_id": file_id,
                    "filename": filename,
                    "error": error_msg,
                })
                return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error=error_msg)
            
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
            if streams > 1 and spec.size_bytes >= DEFAULTS.min_multistream_size_bytes:
                # If a previous partial exists, fall back to single-stream resume
                if dst_tmp.exists() and dst_tmp.stat().st_size < spec.size_bytes:
                    streams = 1
                else:
                    self._copy_multistream(job, src, dst_tmp, spec.size_bytes, streams, file_id)
            else:
                # Resume simple: if .part exists, append from current size
                start_offset = dst_tmp.stat().st_size if dst_tmp.exists() else 0
                mode = "r+b" if dst_tmp.exists() else "wb"
                
                # Add safety check for file opening
                try:
                    with src.open("rb") as rf, dst_tmp.open(mode) as wf:
                        if start_offset:
                            rf.seek(start_offset)
                            wf.seek(start_offset)
                        # Use larger chunks for single-stream copy
                        chunk_size = max(DEFAULTS.io_chunk_size_bytes, 512 * 1024 * 1024)  # At least 512MB chunks for maximum performance
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
                            buf = rf.read(chunk_size)
                            if not buf:
                                break
                            wf.write(buf)
                            self._progress(job.job_id, len(buf), file_id)
                except Exception as e:
                    error_msg = f"File I/O error: {e}"
                    self._logger.error(error_msg)
                    self._emit(job.job_id, "file.failed", {
                        "file_id": file_id,
                        "filename": filename,
                        "error": error_msg,
                    })
                    return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error=error_msg)
            
            # Only verify in BALANCED mode, not in FAST mode
            if (job.options.mode or "BALANCED").upper() == "BALANCED":
                # Verify (BALANCED): xxHash64 source vs dest
                try:
                    src_hash = hash_file_xxh(src)
                    dst_hash = hash_file_xxh(dst_tmp)
                    if src_hash.hexdigest != dst_hash.hexdigest:
                        # NEW: Add verification record for failed verification
                        if job.options.generate_verification_report:
                            self._add_verification_record(job, spec, src_hash, dst_hash, "FAIL", "hash_mismatch")
                        
                        self._emit(job.job_id, "file.failed", {
                            "file_id": file_id,
                            "filename": filename,
                            "error": "hash_mismatch",
                        })
                        return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error="hash_mismatch")
                    hexdigest = src_hash.hexdigest
                    
                    # NEW: Add verification record for successful verification
                    if job.options.generate_verification_report:
                        self._add_verification_record(job, spec, src_hash, dst_hash, "PASS")
                        
                except Exception as e:
                    error_msg = f"Hash verification error: {e}"
                    self._logger.error(error_msg)
                    
                    # NEW: Add verification record for verification error
                    if job.options.generate_verification_report:
                        self._add_verification_record(job, spec, None, None, "FAIL", error_msg)
                    
                    self._emit(job.job_id, "file.failed", {
                        "file_id": file_id,
                        "filename": filename,
                        "error": error_msg,
                    })
                    return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error=error_msg)
            elif (job.options.mode or "BALANCED").upper() == "FAST":
                # FAST mode: size check only, no hashing
                hexdigest = None
                # Quick size verification only
                try:
                    if dst_tmp.stat().st_size != spec.size_bytes:
                        # NEW: Add verification record for failed size verification
                        if job.options.generate_verification_report:
                            self._add_verification_record(job, spec, None, None, "FAIL", "size_mismatch")
                        
                        self._emit(job.job_id, "file.failed", {
                            "file_id": file_id,
                            "filename": filename,
                            "error": "size_mismatch",
                        })
                        return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error="size_mismatch")
                    
                    # NEW: Add verification record for successful size verification
                    if job.options.generate_verification_report:
                        self._add_verification_record(job, spec, None, None, "PASS")
                        
                except Exception as e:
                    error_msg = f"Size verification error: {e}"
                    self._logger.error(error_msg)
                    
                    # NEW: Add verification record for verification error
                    if job.options.generate_verification_report:
                        self._add_verification_record(job, spec, None, None, "FAIL", error_msg)
                    
                    self._emit(job.job_id, "file.failed", {
                        "file_id": file_id,
                        "filename": filename,
                        "error": error_msg,
                    })
                    return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error=error_msg)
            else:
                # NONE mode: absolutely no verification, fastest possible
                hexdigest = None
                # Skip all verification - trust the copy operation
                
                # NEW: Add verification record for NONE mode (always PASS since no verification)
                if job.options.generate_verification_report:
                    self._add_verification_record(job, spec, None, None, "PASS")
            
            # Safe file replacement
            try:
                dst_tmp.replace(dst)
            except Exception as e:
                error_msg = f"Failed to replace file: {e}"
                self._logger.error(error_msg)
                self._emit(job.job_id, "file.failed", {
                    "file_id": file_id,
                    "filename": filename,
                    "error": error_msg,
                })
                return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=False, error=error_msg)
            
            # Emit file completed event
            self._emit(job.job_id, "file.completed", {
                "file_id": file_id,
                "filename": filename,
                "bytes": spec.size_bytes,
                "total": spec.size_bytes,
                "skipped": False,
            })
            
            return _CopyOutcome(src=src, dst=dst, size=spec.size_bytes, ok=True, hexdigest=hexdigest)
        except Exception as exc:  # noqa: BLE001
            error_msg = f"Unexpected error during file copy: {exc}"
            self._logger.error(error_msg)
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

        # Compute ranges with larger chunks for better performance
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
                # Use larger chunks for multi-stream to reduce overhead
                chunk_size = max(DEFAULTS.io_chunk_size_bytes, 128 * 1024 * 1024)  # At least 128MB chunks for maximum performance
                while remaining > 0:
                    if self._cancels.get(job.job_id, threading.Event()).is_set():
                        return
                    if self._pauses.get(job.job_id, threading.Event()).is_set():
                        threading.Event().wait(0.05)
                        continue
                    to_read = min(chunk_size, remaining)
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
                current_time = time.time()
                
                # Calculate and emit performance metrics every 50MB or 0.5 seconds for more responsive updates
                if (stats.copied_bytes - stats.last_emit_bytes >= 50 * 1024 * 1024 or 
                    current_time - stats.last_emit >= 0.5):
                    
                    elapsed = current_time - stats.start_time
                    if elapsed > 0:
                        speed_mbps = (stats.copied_bytes / (1024 * 1024)) / elapsed
                        progress = (stats.copied_bytes / stats.total_bytes) * 100 if stats.total_bytes > 0 else 0
                        
                        # Ensure progress never exceeds 100%
                        progress = min(progress, 100.0)
                        
                        self._emit(job_id, "job.progress", {
                            "bytes_copied": stats.copied_bytes,
                            "total_bytes": stats.total_bytes,
                            "progress_percent": progress,
                            "speed_mbps": speed_mbps,
                            "elapsed_time": elapsed
                        })
                        
                        # Log performance for debugging
                        self._logger.info(f"Transfer progress: {progress:.1f}% - {speed_mbps:.1f} MB/s")
                        
                        stats.last_emit = current_time
                        stats.last_emit_bytes = stats.copied_bytes
        
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
                # Add job_id to payload if not already present
                if 'job_id' not in payload:
                    payload = {"job_id": job_id, **payload}
                self._sink.emit(event_type, payload)
            except Exception as e:
                # Log the error for debugging but don't crash
                self._logger.error(f"Failed to emit {event_type}: {e}")
                # Don't re-raise the exception - just log it and continue
                pass

    def cancel_destination(self, dest_path: str) -> None:
        """Cancel transfers to a specific destination"""
        print(f"DEBUG: PythonCopyEngine.cancel_destination called for: {dest_path}")
        try:
            # Find all job IDs that are copying to this destination
            for job_id in list(self._cancels.keys()):
                print(f"DEBUG: Setting cancel event for job_id: {job_id}")
                cancel_event = self._cancels.get(job_id)
                if cancel_event:
                    cancel_event.set()
                    print(f"DEBUG: Cancel event set for job_id: {job_id}")
        except Exception as e:
            print(f"DEBUG: Error in cancel_destination: {e}")
            import traceback
            traceback.print_exc()

    def get_current_job_id(self) -> Optional[str]:
        """Get the current job ID for UI operations"""
        # Return the most recent job ID or None
        if self._cancels:
            return list(self._cancels.keys())[-1]
        return None


