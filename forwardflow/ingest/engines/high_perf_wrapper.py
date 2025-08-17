"""High Performance Transfer Engine Wrapper

This module provides a Python interface to the high-performance C++ transfer engine
that uses zero-copy techniques, async I/O, and optimized chunking for maximum speeds.
"""

import os
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .high_perf_engine import HighPerfTransferEngine
    HIGH_PERF_AVAILABLE = True
except ImportError:
    HIGH_PERF_AVAILABLE = False
    HighPerfTransferEngine = None

from ..api.interfaces import Engine, EventSink
from ..api.models import JobSpec, FileSpec, Results
from ..policies.simple_policy import SimplePolicy
from ..logging import get_logger


class HighPerfEngine(Engine):
    """High-performance file transfer engine using C++ optimizations."""
    
    def __init__(self, sink: Optional[EventSink] = None) -> None:
        if not HIGH_PERF_AVAILABLE:
            raise RuntimeError("High performance engine not available. Please build the C++ extension first.")
        
        self._logger = get_logger("forwardflow.ingest.engine.high_perf")
        self._engine = HighPerfTransferEngine()
        self._sink = sink
        self._cancelled = False
        self._paused = False
        
        # Set up event sink for C++ engine
        if sink:
            self._engine.set_event_sink(self._emit_event)
    
    def start(self, job: JobSpec) -> None:
        """Start the high-performance transfer job."""
        policy = SimplePolicy()
        files: list[FileSpec] = list(policy.plan(job))
        
        total_bytes = sum(f.size_bytes for f in files)
        start_time = time.time()
        
        self._emit("job.started", {
            "total_bytes": total_bytes,
            "total_files": len(files)
        })
        
        # Use ThreadPoolExecutor for parallel file transfers
        max_workers = min(32, len(files))  # Cap at 32 workers
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file transfers
            future_to_file = {
                executor.submit(self._transfer_single_file, job, file_spec): file_spec
                for file_spec in files
            }
            
            completed_files = 0
            total_copied = 0
            
            # Process completed transfers
            for future in as_completed(future_to_file):
                if self._cancelled:
                    break
                
                file_spec = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        completed_files += 1
                        total_copied += file_spec.size_bytes
                        
                        # Emit progress
                        progress = (total_copied / total_bytes) * 100
                        elapsed = time.time() - start_time
                        speed_mbps = (total_copied / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                        
                        self._emit("job.progress", {
                            "bytes_copied": total_copied,
                            "total_bytes": total_bytes,
                            "progress_percent": progress,
                            "speed_mbps": speed_mbps,
                            "elapsed_time": elapsed
                        })
                        
                        self._logger.info(f"File completed: {file_spec.filename} - Progress: {progress:.1f}% - Speed: {speed_mbps:.1f} MB/s")
                    
                except Exception as e:
                    self._logger.error(f"File transfer failed: {file_spec.filename} - {e}")
                    self._emit("file.failed", {
                        "file_id": f"{job.job_id}_{file_spec.filename}",
                        "filename": file_spec.filename,
                        "error": str(e)
                    })
        
        # Job completed
        elapsed = time.time() - start_time
        final_speed = (total_copied / (1024 * 1024)) / elapsed if elapsed > 0 else 0
        
        self._emit("job.completed", {
            "bytes": total_copied,
            "total": total_bytes,
            "elapsed_s": elapsed,
            "mbps": final_speed
        })
        
        self._logger.info(f"Job completed: {total_copied} bytes in {elapsed:.1f}s at {final_speed:.1f} MB/s")
    
    def _transfer_single_file(self, job: JobSpec, file_spec: FileSpec) -> bool:
        """Transfer a single file using the high-performance engine."""
        try:
            src_path = str(file_spec.source)
            dst_path = str(file_spec.destination)
            
            # Create destination directory if needed
            dst_dir = Path(dst_path).parent
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            # Use the C++ engine for maximum performance
            success = self._engine.transfer_file(
                src_path, dst_path, file_spec.size_bytes,
                f"{job.job_id}_{file_spec.filename}"
            )
            
            return success
            
        except Exception as e:
            self._logger.error(f"Error transferring {file_spec.filename}: {e}")
            return False
    
    def pause(self, job_id: str) -> None:
        """Pause the transfer."""
        self._paused = True
        if self._engine:
            self._engine.pause()
        self._logger.info(f"Transfer paused for job: {job_id}")
    
    def resume(self, job_id: str) -> None:
        """Resume the transfer."""
        self._paused = False
        if self._engine:
            self._engine.resume()
        self._logger.info(f"Transfer resumed for job: {job_id}")
    
    def cancel(self, job_id: str) -> None:
        """Cancel the transfer."""
        self._cancelled = True
        if self._engine:
            self._engine.cancel()
        self._logger.info(f"Transfer cancelled for job: {job_id}")
    
    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit an event through the sink."""
        if self._sink:
            self._sink.emit(event_type, payload)


def is_available() -> bool:
    """Check if the high-performance engine is available."""
    return HIGH_PERF_AVAILABLE


def get_engine_class():
    """Get the high-performance engine class if available."""
    return HighPerfEngine if HIGH_PERF_AVAILABLE else None
