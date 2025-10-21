#!/usr/bin/env python3
"""
JobAggregator: Professional progress tracking for multi-file transfers
"""

import time
import collections
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass


@dataclass
class FileProgress:
    """Individual file progress tracking"""
    file_id: str
    dest_path: str
    dest_key: str
    total_bytes: int
    bytes_copied: int = 0
    dest_index: Optional[int] = None
    completed: bool = False
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class DestinationMetrics:
    """Per-destination aggregate metrics"""
    dest_path: str
    bytes_copied: int = 0  # Bytes actually written and confirmed
    total_bytes: int = 0    # Bytes discovered so far for this destination
    expected_total_bytes: int = 0  # Stable denominator sourced from manifest if available
    completed_files: int = 0
    total_files: int = 0
    current_mb_s: float = 0.0
    peak_mb_s: float = 0.0
    eta_seconds: float = 0.0
    window: collections.deque = None
    
    def __post_init__(self):
        if self.window is None:
            # 2-3 second moving window at ~10 updates/sec = 20-30 samples
            self.window = collections.deque(maxlen=25)


@dataclass
class JobSnapshot:
    """Immutable snapshot of current job state for UI updates"""
    # Job-level metrics
    job_progress_percent: float
    job_bytes_copied: int
    job_total_bytes: int
    job_completed_files: int
    job_total_files: int
    job_current_mb_s: float
    job_avg_mb_s: float
    job_peak_mb_s: float
    job_eta_seconds: float
    job_elapsed_seconds: float
    
    # Per-destination metrics
    destinations: Dict[str, DestinationMetrics]
    
    # Current file being processed
    current_filename: str = ""


class JobAggregator:
    """
    Professional job progress aggregator with smooth throughput tracking
    
    Maintains accurate job-level and per-destination progress without resets.
    Uses moving-window rate calculation for smooth throughput metrics.
    """
    
    def __init__(self, total_files: int, destinations: List[str], dataset_total_bytes: int = 0):
        self.started_at = time.monotonic()
        self.destinations = destinations
        self.destination_count = max(1, len(destinations))
        self.initial_total_files = max(0, total_files)
        self.dataset_total_bytes = max(0, dataset_total_bytes)
        
        # File tracking: (file_id, dest_key) -> FileProgress
        self.files: Dict[Tuple[str, str], FileProgress] = {}
        self.file_destinations: Dict[str, Set[str]] = {}
        self.file_totals: Dict[str, int] = {}
        self.completed_transfers = 0
        self._shared_file_ids_detected = self.destination_count > 1
        
        # Per-destination tracking: dest_path -> DestinationMetrics
        self.dest_metrics: Dict[str, DestinationMetrics] = {}
        for dest in destinations:
            self.dest_metrics[dest] = DestinationMetrics(
                dest_path=dest,
                expected_total_bytes=self.dataset_total_bytes,
                total_files=self.initial_total_files
            )
        
        # Job-level smoothing window: (timestamp, total_bytes_copied)
        self.job_window = collections.deque(maxlen=25)  # ~2.5s at 10 updates/sec
        self.job_peak_mb_s = 0.0
        
        # Current state
        self.current_filename = ""
        
        print(f"DEBUG: JobAggregator initialized for {total_files} files to {len(destinations)} destinations")
    
    def _normalize_destination(self, dest_path: str, dest_index: Optional[int]) -> str:
        """Return a stable destination identifier for tracking."""
        if dest_path:
            return dest_path
        if dest_index is not None and 0 <= dest_index < len(self.destinations):
            return self.destinations[dest_index]
        # Fallback identifier to ensure we never lose tracking
        return f"__dest_{dest_index if dest_index is not None else 0}"
    
    def _ensure_destination_metrics(self, dest_path: str) -> DestinationMetrics:
        """Ensure a DestinationMetrics entry exists for the given path."""
        if dest_path not in self.dest_metrics:
            self.dest_metrics[dest_path] = DestinationMetrics(
                dest_path=dest_path,
                expected_total_bytes=self.dataset_total_bytes,
                total_files=self.initial_total_files
            )
        return self.dest_metrics[dest_path]

    def _refresh_expected_totals(self) -> None:
        """Propagate dataset total bytes to all destination metrics."""
        if self.dataset_total_bytes <= 0:
            return
        for metrics in self.dest_metrics.values():
            if metrics.expected_total_bytes < self.dataset_total_bytes:
                metrics.expected_total_bytes = self.dataset_total_bytes
                if metrics.total_bytes > metrics.expected_total_bytes:
                    metrics.expected_total_bytes = metrics.total_bytes

    def apply_manifest_hint(self, total_files: int, dataset_total_bytes: int) -> None:
        """Update aggregator with manifest-derived totals without resetting state."""
        if total_files > 0:
            self.initial_total_files = max(self.initial_total_files, total_files)
            for metrics in self.dest_metrics.values():
                metrics.total_files = max(metrics.total_files, total_files)
        if dataset_total_bytes > 0:
            if dataset_total_bytes > self.dataset_total_bytes:
                self.dataset_total_bytes = dataset_total_bytes
                self._refresh_expected_totals()
    
    def _calculate_job_totals(self) -> Tuple[int, int]:
        """Aggregate job-level byte totals across all destinations."""
        job_copied_bytes = sum(dest.bytes_copied for dest in self.dest_metrics.values())
        discovered_total = sum(dest.total_bytes for dest in self.dest_metrics.values())
        expected_from_metrics = sum(
            (dest.expected_total_bytes or dest.total_bytes) for dest in self.dest_metrics.values()
        )

        dataset_total = self.dataset_total_bytes
        if dataset_total <= 0 and self.file_totals:
            dataset_total = sum(self.file_totals.values())
            if dataset_total > self.dataset_total_bytes:
                self.dataset_total_bytes = dataset_total
                self._refresh_expected_totals()

        expected_total = 0
        if dataset_total > 0:
            expected_total = dataset_total * self.destination_count
        expected_total = max(expected_total, expected_from_metrics)

        job_total_bytes = max(discovered_total, expected_total)
        if job_total_bytes <= 0:
            job_total_bytes = discovered_total
        if job_total_bytes <= 0:
            job_total_bytes = 0

        job_copied_bytes = min(job_copied_bytes, job_total_bytes) if job_total_bytes > 0 else job_copied_bytes
        return job_total_bytes, job_copied_bytes
    
    def _calculate_job_file_counts(self) -> Tuple[int, int]:
        """Calculate job-level file counts including per-destination work."""
        destination_multiplier = self.destination_count
        expected_total = self.initial_total_files * destination_multiplier if self.initial_total_files > 0 else 0

        # Fall back to discovered file counts when manifest totals are unavailable
        if expected_total <= 0:
            expected_total = len(self.files)
        else:
            expected_total = max(expected_total, len(self.files))

        completed_files = min(self.completed_transfers, expected_total)
        return expected_total, completed_files
    
    def update_file_progress(self, file_id: str, bytes_copied: int, total_bytes: int,
                             dest_path: str, filename: str = "", dest_index: Optional[int] = None) -> JobSnapshot:
        """
        Update progress for a specific file and return current job snapshot
        
        Args:
            file_id: Unique file identifier
            bytes_copied: Bytes copied for this file
            total_bytes: Total bytes for this file  
            dest_path: Destination path for this file
            filename: Display name for current file
            dest_index: Destination index for this file (if provided by engine)
            
        Returns:
            JobSnapshot with current state for UI updates
        """
        now = time.monotonic()
        self.current_filename = filename
        
        resolved_dest_path = self._normalize_destination(dest_path, dest_index)
        file_key = (file_id, resolved_dest_path)
        
        file_progress = self.files.get(file_key)
        if file_progress is None:
            file_progress = FileProgress(
                file_id=file_id,
                dest_path=resolved_dest_path,
                dest_key=resolved_dest_path,
                total_bytes=total_bytes,
                bytes_copied=0,
                dest_index=dest_index,
                started_at=now
            )
            self.files[file_key] = file_progress
            self.file_totals[file_id] = max(total_bytes, self.file_totals.get(file_id, 0))
            dest_set = self.file_destinations.setdefault(file_id, set())
            dest_set.add(resolved_dest_path)
            if len(dest_set) > 1:
                self._shared_file_ids_detected = True
            print(f"DEBUG: JobAggregator tracking new file {file_id} ({total_bytes} bytes) -> {resolved_dest_path}")
        else:
            if total_bytes > file_progress.total_bytes:
                file_progress.total_bytes = total_bytes
            self.file_totals[file_id] = max(total_bytes, self.file_totals.get(file_id, 0))
            if dest_index is not None:
                file_progress.dest_index = dest_index

        # Keep a monotonic dataset total estimate (per-source bytes, not multiplied by destinations)
        discovered_total = sum(self.file_totals.values())
        if discovered_total > self.dataset_total_bytes:
            self.dataset_total_bytes = discovered_total
            self._refresh_expected_totals()
        
        old_bytes = file_progress.bytes_copied
        new_bytes = max(old_bytes, bytes_copied)
        file_progress.bytes_copied = new_bytes
        
        if new_bytes >= file_progress.total_bytes and not file_progress.completed:
            file_progress.completed = True
            file_progress.completed_at = now
            self.completed_transfers += 1
            print(f"DEBUG: File {file_id} completed for {resolved_dest_path} ({new_bytes}/{file_progress.total_bytes} bytes)")
        
        dest_metrics = self._ensure_destination_metrics(resolved_dest_path)
        bytes_delta = max(0, new_bytes - old_bytes)
        dest_metrics.bytes_copied += bytes_delta
        
        dest_files = [f for f in self.files.values() if f.dest_key == resolved_dest_path]
        discovered_files = len(dest_files)
        dest_metrics.total_files = max(dest_metrics.total_files, discovered_files)
        dest_metrics.completed_files = sum(1 for f in dest_files if f.completed)
        dest_metrics.total_bytes = sum(f.total_bytes for f in dest_files)
        if self.dataset_total_bytes > 0:
            dest_metrics.expected_total_bytes = max(dest_metrics.expected_total_bytes, self.dataset_total_bytes)
        else:
            dest_metrics.expected_total_bytes = max(dest_metrics.expected_total_bytes, dest_metrics.total_bytes)
        
        dest_metrics.window.append((now, dest_metrics.bytes_copied))
        dest_metrics.current_mb_s = self._calculate_rate_mb_s(dest_metrics.window)
        dest_metrics.peak_mb_s = max(dest_metrics.peak_mb_s, dest_metrics.current_mb_s)
        
        if dest_metrics.current_mb_s > 0 and dest_metrics.bytes_copied < dest_metrics.total_bytes:
            remaining_bytes = dest_metrics.total_bytes - dest_metrics.bytes_copied
            dest_metrics.eta_seconds = remaining_bytes / (dest_metrics.current_mb_s * 1024 * 1024)
        else:
            dest_metrics.eta_seconds = 0.0
        
        job_total_bytes, job_copied_bytes = self._calculate_job_totals()
        
        self.job_window.append((now, job_copied_bytes))
        job_current_mb_s = self._calculate_rate_mb_s(self.job_window)
        self.job_peak_mb_s = max(self.job_peak_mb_s, job_current_mb_s)
        
        elapsed_seconds = now - self.started_at
        job_avg_mb_s = (job_copied_bytes / (1024 * 1024)) / elapsed_seconds if elapsed_seconds > 0 else 0.0
        
        if job_current_mb_s > 0 and job_copied_bytes < job_total_bytes:
            remaining_bytes = job_total_bytes - job_copied_bytes
            job_eta_seconds = remaining_bytes / (job_current_mb_s * 1024 * 1024)
        else:
            job_eta_seconds = 0.0
        
        job_progress_percent = (job_copied_bytes / job_total_bytes * 100.0) if job_total_bytes > 0 else 0.0
        job_progress_percent = min(100.0, max(0.0, job_progress_percent))
        
        job_total_files, job_completed_files = self._calculate_job_file_counts()
        
        snapshot = JobSnapshot(
            job_progress_percent=job_progress_percent,
            job_bytes_copied=job_copied_bytes,
            job_total_bytes=job_total_bytes,
            job_completed_files=job_completed_files,
            job_total_files=job_total_files,
            job_current_mb_s=job_current_mb_s,
            job_avg_mb_s=job_avg_mb_s,
            job_peak_mb_s=self.job_peak_mb_s,
            job_eta_seconds=job_eta_seconds,
            job_elapsed_seconds=elapsed_seconds,
            destinations=dict(self.dest_metrics),
            current_filename=self.current_filename
        )
        
        return snapshot
    
    def _calculate_rate_mb_s(self, window: collections.deque) -> float:
        """
        Calculate current transfer rate from moving window
        
        Args:
            window: Deque of (timestamp, bytes_copied) tuples
            
        Returns:
            Current rate in MB/s
        """
        if len(window) < 2:
            return 0.0
        
        # Use oldest and newest samples for rate calculation
        oldest_time, oldest_bytes = window[0]
        newest_time, newest_bytes = window[-1]
        
        time_delta = newest_time - oldest_time
        bytes_delta = newest_bytes - oldest_bytes
        
        if time_delta <= 0:
            return 0.0
        
        # Convert to MB/s
        rate_mb_s = (bytes_delta / (1024 * 1024)) / time_delta
        return max(0.0, rate_mb_s)  # Never negative
    
    def get_current_snapshot(self) -> JobSnapshot:
        """Get current job state without updating any progress"""
        job_total_bytes, job_copied_bytes = self._calculate_job_totals()
        
        elapsed_seconds = time.monotonic() - self.started_at
        job_current_mb_s = self._calculate_rate_mb_s(self.job_window)
        job_avg_mb_s = (job_copied_bytes / (1024 * 1024)) / elapsed_seconds if elapsed_seconds > 0 else 0.0
        
        if job_current_mb_s > 0 and job_copied_bytes < job_total_bytes:
            remaining_bytes = job_total_bytes - job_copied_bytes
            job_eta_seconds = remaining_bytes / (job_current_mb_s * 1024 * 1024)
        else:
            job_eta_seconds = 0.0
        
        job_progress_percent = (job_copied_bytes / job_total_bytes * 100.0) if job_total_bytes > 0 else 0.0
        job_progress_percent = min(100.0, max(0.0, job_progress_percent))
        job_total_files, job_completed_files = self._calculate_job_file_counts()
        
        return JobSnapshot(
            job_progress_percent=job_progress_percent,
            job_bytes_copied=job_copied_bytes,
            job_total_bytes=job_total_bytes,
            job_completed_files=job_completed_files,
            job_total_files=job_total_files,
            job_current_mb_s=job_current_mb_s,
            job_avg_mb_s=job_avg_mb_s,
            job_peak_mb_s=self.job_peak_mb_s,
            job_eta_seconds=job_eta_seconds,
            job_elapsed_seconds=elapsed_seconds,
            destinations=dict(self.dest_metrics),
            current_filename=self.current_filename
        )
    
    def get_comprehensive_stats_for_reporting(self) -> Dict[str, Any]:
        """Get comprehensive stats formatted for DIT report generation"""
        snapshot = self.get_current_snapshot()
        
        # Convert file progress data to report format
        file_records = []
        for (file_id, _), file_progress in self.files.items():
            # Determine transfer status for report generator
            if file_progress.completed:
                transfer_status = 'COMPLETED'
                verification_status = 'COMPLETED'  # Assume verification passed for completed files
            else:
                transfer_status = 'IN_PROGRESS'
                verification_status = 'PENDING'
            
            file_records.append({
                'filename': file_progress.file_id,
                'size_bytes': file_progress.total_bytes,
                'bytes_copied': file_progress.bytes_copied,
                'completed': file_progress.completed,
                'transfer_status': transfer_status,  # Required by report generator
                'status': transfer_status,  # Also provide direct status field
                'dest_path': file_progress.dest_path,
                'started_at': file_progress.started_at,
                'completed_at': file_progress.completed_at,
                'transfer_speed_mbps': 0.0,  # Calculate if needed
                'verification_status': verification_status,
                'checksum_source': '',
                'checksum_dest': '',
                'checksum': '',  # Empty for now, will be calculated by report generator
                'checksum_algorithm': 'xxHash64BE'
            })
        
        # Prepare comprehensive stats
        stats = {
            'total_bytes': snapshot.job_total_bytes,
            'copied_bytes': snapshot.job_bytes_copied,
            'duration_seconds': snapshot.job_elapsed_seconds,
            'avg_speed_mb_s': snapshot.job_avg_mb_s,
            'peak_speed_mb_s': snapshot.job_peak_mb_s,
            'total_files': snapshot.job_total_files,
            'completed_files': snapshot.job_completed_files,
            'cancelled_files': 0,  # Track separately if needed
            'error_files': 0,      # Track separately if needed
            'progress_percent': snapshot.job_progress_percent,
            'eta_seconds': snapshot.job_eta_seconds,
            'current_speed_mb_s': snapshot.job_current_mb_s
        }
        
        # Per-destination statistics
        dest_stats = {}
        for dest_path, dest_metrics in snapshot.destinations.items():
            expected_total = dest_metrics.expected_total_bytes or dest_metrics.total_bytes
            progress_percent = (
                (dest_metrics.bytes_copied / expected_total) * 100
            ) if expected_total > 0 else 0.0
            dest_stats[dest_path] = {
                'bytes_copied': dest_metrics.bytes_copied,
                'total_bytes': expected_total,
                'completed_files': dest_metrics.completed_files,
                'total_files': dest_metrics.total_files,
                'current_speed_mb_s': dest_metrics.current_mb_s,
                'peak_speed_mb_s': dest_metrics.peak_mb_s,
                'progress_percent': progress_percent,
                'is_completed': dest_metrics.completed_files >= dest_metrics.total_files and dest_metrics.total_files > 0
            }
        
        return {
            'stats': stats,
            'files': file_records,
            'destinations': dest_stats,
            'started_at': self.started_at,
            'snapshot_time': time.monotonic()
        }
    
    def get_destination_completion_status(self) -> Dict[str, bool]:
        """Check which destinations have completed their transfers"""
        completion_status = {}
        for dest_path, dest_metrics in self.dest_metrics.items():
            is_completed = (dest_metrics.completed_files >= dest_metrics.total_files and 
                          dest_metrics.total_files > 0)
            completion_status[dest_path] = is_completed
        return completion_status
    
    def reset_for_new_job(self, total_files: int, destinations: List[str], dataset_total_bytes: int = 0):
        """Reset aggregator for a new transfer job"""
        self.started_at = time.monotonic()
        self.initial_total_files = max(0, total_files)
        self.destinations = destinations
        self.destination_count = max(1, len(destinations))
        self.dataset_total_bytes = max(0, dataset_total_bytes)
        self.files.clear()
        self.file_destinations.clear()
        self.file_totals.clear()
        self.completed_transfers = 0
        self._shared_file_ids_detected = self.destination_count > 1
        self.dest_metrics.clear()
        for dest in destinations:
            self.dest_metrics[dest] = DestinationMetrics(
                dest_path=dest,
                expected_total_bytes=self.dataset_total_bytes,
                total_files=self.initial_total_files
            )
        self.job_window.clear()
        self.job_peak_mb_s = 0.0
        self.current_filename = ""
        
        print(f"DEBUG: JobAggregator reset for new job: {total_files} files to {len(destinations)} destinations")
