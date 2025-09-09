#!/usr/bin/env python3
"""
JobAggregator: Professional progress tracking for multi-file transfers
"""

import time
import collections
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class FileProgress:
    """Individual file progress tracking"""
    file_id: str
    bytes_copied: int
    total_bytes: int
    dest_path: str
    completed: bool = False
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class DestinationMetrics:
    """Per-destination aggregate metrics"""
    dest_path: str
    bytes_copied: int = 0
    total_bytes: int = 0
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
    
    def __init__(self, total_files: int, destinations: List[str]):
        self.started_at = time.monotonic()
        self.total_files = total_files
        self.destinations = destinations
        
        # File tracking: file_id -> FileProgress
        self.files: Dict[str, FileProgress] = {}
        self.completed_files = 0
        
        # Per-destination tracking: dest_path -> DestinationMetrics
        self.dest_metrics: Dict[str, DestinationMetrics] = {}
        for dest in destinations:
            self.dest_metrics[dest] = DestinationMetrics(dest_path=dest)
        
        # Job-level smoothing window: (timestamp, total_bytes_copied)
        self.job_window = collections.deque(maxlen=25)  # ~2.5s at 10 updates/sec
        self.job_peak_mb_s = 0.0
        
        # Current state
        self.current_filename = ""
        
        print(f"DEBUG: JobAggregator initialized for {total_files} files to {len(destinations)} destinations")
    
    def update_file_progress(self, file_id: str, bytes_copied: int, total_bytes: int, 
                           dest_path: str, filename: str = "") -> JobSnapshot:
        """
        Update progress for a specific file and return current job snapshot
        
        Args:
            file_id: Unique file identifier
            bytes_copied: Bytes copied for this file
            total_bytes: Total bytes for this file  
            dest_path: Destination path for this file
            filename: Display name for current file
            
        Returns:
            JobSnapshot with current state for UI updates
        """
        now = time.monotonic()
        self.current_filename = filename
        
        # Update or create file progress
        if file_id not in self.files:
            self.files[file_id] = FileProgress(
                file_id=file_id,
                bytes_copied=0,
                total_bytes=total_bytes,
                dest_path=dest_path,
                started_at=now
            )
            print(f"DEBUG: JobAggregator tracking new file {file_id} ({total_bytes} bytes) -> {dest_path}")
        
        file_progress = self.files[file_id]
        old_bytes = file_progress.bytes_copied
        file_progress.bytes_copied = bytes_copied
        
        # Mark as completed if fully copied
        if bytes_copied >= total_bytes and not file_progress.completed:
            file_progress.completed = True
            file_progress.completed_at = now
            self.completed_files += 1
            print(f"DEBUG: File {file_id} completed ({bytes_copied}/{total_bytes} bytes)")
        
        # Update destination metrics
        if dest_path in self.dest_metrics:
            dest_metrics = self.dest_metrics[dest_path]
            
            # Update destination byte totals
            bytes_delta = bytes_copied - old_bytes
            dest_metrics.bytes_copied += bytes_delta
            
            print(f"DEBUG: *** DESTINATION METRICS UPDATE ***")
            print(f"DEBUG: dest_path: {dest_path}")
            print(f"DEBUG: bytes_delta: {bytes_delta} (new: {bytes_copied}, old: {old_bytes})")
            print(f"DEBUG: dest_metrics.bytes_copied: {dest_metrics.bytes_copied}")
            
            # Update destination file counts (count unique files assigned to this dest)
            dest_files = [f for f in self.files.values() if f.dest_path == dest_path]
            dest_metrics.total_files = len(dest_files)
            dest_metrics.completed_files = sum(1 for f in dest_files if f.completed)
            
            # Add to destination window for rate calculation
            dest_metrics.window.append((now, dest_metrics.bytes_copied))
            
            # Calculate destination current rate
            dest_metrics.current_mb_s = self._calculate_rate_mb_s(dest_metrics.window)
            dest_metrics.peak_mb_s = max(dest_metrics.peak_mb_s, dest_metrics.current_mb_s)
            
            print(f"DEBUG: dest_metrics.current_mb_s: {dest_metrics.current_mb_s}")
            print(f"DEBUG: dest_metrics.peak_mb_s: {dest_metrics.peak_mb_s}")
            print(f"DEBUG: dest_metrics.total_bytes: {dest_metrics.total_bytes}")
            
            # Calculate destination ETA
            if dest_metrics.current_mb_s > 0 and dest_metrics.bytes_copied < dest_metrics.total_bytes:
                remaining_bytes = dest_metrics.total_bytes - dest_metrics.bytes_copied
                dest_metrics.eta_seconds = remaining_bytes / (dest_metrics.current_mb_s * 1024 * 1024)
            else:
                dest_metrics.eta_seconds = 0.0
                
            print(f"DEBUG: dest_metrics.eta_seconds: {dest_metrics.eta_seconds}")
        else:
            print(f"DEBUG: *** DESTINATION NOT FOUND IN METRICS: {dest_path} ***")
            print(f"DEBUG: Available destinations: {list(self.dest_metrics.keys())}")
        
        # Update job-level metrics
        job_total_bytes = sum(f.total_bytes for f in self.files.values())
        job_copied_bytes = sum(f.bytes_copied for f in self.files.values())
        
        # Update destination total bytes (may change as new files are discovered)
        for dest_path in self.dest_metrics:
            dest_files = [f for f in self.files.values() if f.dest_path == dest_path]
            self.dest_metrics[dest_path].total_bytes = sum(f.total_bytes for f in dest_files)
        
        # Add to job window for rate calculation
        self.job_window.append((now, job_copied_bytes))
        
        # Calculate job-level rates
        job_current_mb_s = self._calculate_rate_mb_s(self.job_window)
        self.job_peak_mb_s = max(self.job_peak_mb_s, job_current_mb_s)
        
        # Calculate job-level averages and ETA
        elapsed_seconds = now - self.started_at
        job_avg_mb_s = (job_copied_bytes / (1024 * 1024)) / elapsed_seconds if elapsed_seconds > 0 else 0.0
        
        if job_current_mb_s > 0 and job_copied_bytes < job_total_bytes:
            remaining_bytes = job_total_bytes - job_copied_bytes
            job_eta_seconds = remaining_bytes / (job_current_mb_s * 1024 * 1024)
        else:
            job_eta_seconds = 0.0
        
        # Calculate job progress percentage
        job_progress_percent = (job_copied_bytes / job_total_bytes * 100) if job_total_bytes > 0 else 0.0
        
        # Create immutable snapshot for UI
        snapshot = JobSnapshot(
            job_progress_percent=job_progress_percent,
            job_bytes_copied=job_copied_bytes,
            job_total_bytes=job_total_bytes,
            job_completed_files=self.completed_files,
            job_total_files=self.total_files,
            job_current_mb_s=job_current_mb_s,
            job_avg_mb_s=job_avg_mb_s,
            job_peak_mb_s=self.job_peak_mb_s,
            job_eta_seconds=job_eta_seconds,
            job_elapsed_seconds=elapsed_seconds,
            destinations=dict(self.dest_metrics),  # Copy destination metrics
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
        job_total_bytes = sum(f.total_bytes for f in self.files.values())
        job_copied_bytes = sum(f.bytes_copied for f in self.files.values())
        
        elapsed_seconds = time.monotonic() - self.started_at
        job_current_mb_s = self._calculate_rate_mb_s(self.job_window)
        job_avg_mb_s = (job_copied_bytes / (1024 * 1024)) / elapsed_seconds if elapsed_seconds > 0 else 0.0
        
        if job_current_mb_s > 0 and job_copied_bytes < job_total_bytes:
            remaining_bytes = job_total_bytes - job_copied_bytes
            job_eta_seconds = remaining_bytes / (job_current_mb_s * 1024 * 1024)
        else:
            job_eta_seconds = 0.0
        
        job_progress_percent = (job_copied_bytes / job_total_bytes * 100) if job_total_bytes > 0 else 0.0
        
        return JobSnapshot(
            job_progress_percent=job_progress_percent,
            job_bytes_copied=job_copied_bytes,
            job_total_bytes=job_total_bytes,
            job_completed_files=self.completed_files,
            job_total_files=self.total_files,
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
        for file_id, file_progress in self.files.items():
            file_records.append({
                'filename': file_id,
                'size_bytes': file_progress.total_bytes,
                'bytes_copied': file_progress.bytes_copied,
                'completed': file_progress.completed,
                'dest_path': file_progress.dest_path,
                'started_at': file_progress.started_at,
                'completed_at': file_progress.completed_at,
                'transfer_speed_mbps': 0.0,  # Calculate if needed
                'verification_status': 'PENDING',  # Will be updated by verification
                'checksum_source': '',
                'checksum_dest': ''
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
            dest_stats[dest_path] = {
                'bytes_copied': dest_metrics.bytes_copied,
                'total_bytes': dest_metrics.total_bytes,
                'completed_files': dest_metrics.completed_files,
                'total_files': dest_metrics.total_files,
                'current_speed_mb_s': dest_metrics.current_mb_s,
                'peak_speed_mb_s': dest_metrics.peak_mb_s,
                'progress_percent': (dest_metrics.bytes_copied / dest_metrics.total_bytes * 100) if dest_metrics.total_bytes > 0 else 0.0,
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
    
    def reset_for_new_job(self, total_files: int, destinations: List[str]):
        """Reset aggregator for a new transfer job"""
        self.started_at = time.monotonic()
        self.total_files = total_files
        self.destinations = destinations
        self.files.clear()
        self.completed_files = 0
        self.dest_metrics.clear()
        for dest in destinations:
            self.dest_metrics[dest] = DestinationMetrics(dest_path=dest)
        self.job_window.clear()
        self.job_peak_mb_s = 0.0
        self.current_filename = ""
        
        print(f"DEBUG: JobAggregator reset for new job: {total_files} files to {len(destinations)} destinations")