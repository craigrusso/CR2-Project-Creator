#!/usr/bin/env python3
"""
JobState: Single source of truth for stable progress tracking
Implements the JobManifest approach to prevent progress bar resets
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import time


@dataclass
class JobState:
    """
    Single source of truth for job progress
    Initialized once with manifest data and never changes total_target_bytes
    """
    job_id: str
    total_files: int
    total_bytes: int
    destination_count: int
    total_target_bytes: int
    bytes_copied: int = 0
    completed_files: int = 0
    current_speed_mbps: float = 0.0
    peak_speed_mbps: float = 0.0
    elapsed_seconds: float = 0.0
    eta_seconds: float = 0.0
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage - guaranteed stable denominator"""
        if self.total_target_bytes == 0:
            return 0.0
        return 100.0 * (self.bytes_copied / self.total_target_bytes)
    
    @property
    def files_progress_percent(self) -> float:
        """Calculate file count progress percentage"""
        if self.total_files == 0:
            return 0.0
        return 100.0 * (self.completed_files / self.total_files)
    
    def validate_progress_update(self, total_target_bytes: int) -> bool:
        """Validate that progress update matches our immutable manifest"""
        if total_target_bytes != self.total_target_bytes:
            print(f"ERROR: Progress update total_target_bytes mismatch: "
                  f"expected {self.total_target_bytes}, got {total_target_bytes}")
            return False
        return True


class JobStateManager:
    """
    Manages JobState with strict immutability guarantees
    Prevents progress bar jumps by enforcing stable denominators
    """
    
    def __init__(self):
        self.current_state: Optional[JobState] = None
        self.start_time: Optional[float] = None
        self.last_progress_log_time: float = 0.0
        self.progress_log_interval: float = 2.0  # Log every 2 seconds
    
    def initialize_from_manifest(self, manifest_payload: Dict[str, Any]) -> bool:
        """
        Initialize JobState from job.start manifest
        
        Args:
            manifest_payload: job.start event payload with immutable totals
            
        Returns:
            True if initialization succeeded
        """
        try:
            self.current_state = JobState(
                job_id=manifest_payload["job_id"],
                total_files=manifest_payload["total_files"],
                total_bytes=manifest_payload["total_bytes"],
                destination_count=manifest_payload["destination_count"],
                total_target_bytes=manifest_payload["total_target_bytes"]
            )
            self.start_time = time.time()
            
            print(f"JobState initialized: {self.current_state.total_files} files, "
                  f"{self.current_state.total_target_bytes} target bytes")
            return True
            
        except KeyError as e:
            print(f"ERROR: JobState initialization failed, missing key: {e}")
            return False
        except Exception as e:
            print(f"ERROR: JobState initialization failed: {e}")
            return False
    
    def update_progress(self, progress_payload: Dict[str, Any]) -> bool:
        """
        Update progress from job.progress event
        
        Args:
            progress_payload: job.progress event payload
            
        Returns:
            True if update was valid and applied
        """
        if not self.current_state:
            print("WARNING: JobState not initialized, cannot update progress")
            return False
        
        try:
            # Validate against manifest
            total_target_bytes = progress_payload.get("total_target_bytes")
            if total_target_bytes and not self.current_state.validate_progress_update(total_target_bytes):
                return False
            
            # Update mutable fields only
            self.current_state.bytes_copied = progress_payload.get("bytes_copied", 0)
            self.current_state.completed_files = progress_payload.get("completed_files", 0)
            self.current_state.current_speed_mbps = progress_payload.get("current_speed_mbps", 0.0)
            self.current_state.peak_speed_mbps = progress_payload.get("peak_speed_mbps", 0.0)
            self.current_state.elapsed_seconds = progress_payload.get("elapsed_seconds", 0.0)
            self.current_state.eta_seconds = progress_payload.get("eta_seconds", 0.0)
            
            # Periodic logging to track progress stability
            current_time = time.time()
            if current_time - self.last_progress_log_time >= self.progress_log_interval:
                print(f"JobState progress: {self.current_state.progress_percent:.1f}% "
                      f"({self.current_state.bytes_copied}/{self.current_state.total_target_bytes} bytes)")
                self.last_progress_log_time = current_time
            
            return True
            
        except Exception as e:
            print(f"ERROR: JobState progress update failed: {e}")
            return False
    
    def get_ui_payload(self) -> Dict[str, Any]:
        """
        Get payload for UI updates with stable progress calculation
        
        Returns:
            Dictionary suitable for progress bar updates
        """
        if not self.current_state:
            return {
                "progress_percent": 0.0,
                "bytes_copied": 0,
                "total_target_bytes": 0,
                "completed_files": 0,
                "total_files": 0,
                "current_speed_mbps": 0.0,
                "peak_speed_mbps": 0.0,
                "elapsed_seconds": 0.0,
                "eta_seconds": 0.0
            }
        
        return {
            "progress_percent": self.current_state.progress_percent,
            "bytes_copied": self.current_state.bytes_copied,
            "total_target_bytes": self.current_state.total_target_bytes,
            "completed_files": self.current_state.completed_files,
            "total_files": self.current_state.total_files,
            "current_speed_mbps": self.current_state.current_speed_mbps,
            "peak_speed_mbps": self.current_state.peak_speed_mbps,
            "elapsed_seconds": self.current_state.elapsed_seconds,
            "eta_seconds": self.current_state.eta_seconds,
            "files_progress_percent": self.current_state.files_progress_percent
        }
    
    def reset(self):
        """Reset for new job"""
        self.current_state = None
        self.start_time = None
        self.last_progress_log_time = 0.0
        print("JobState reset for new job")
    
    def is_initialized(self) -> bool:
        """Check if JobState is properly initialized"""
        return self.current_state is not None
    
    def get_state(self) -> Optional[JobState]:
        """Get current JobState (read-only access)"""
        return self.current_state


# Global instance for application use
job_state_manager = JobStateManager()