#!/usr/bin/env python3
"""
Enhanced Multi-Destination Transfer Engine
Optimizes transfers for different destination types with memory buffering
"""

import threading
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import hashlib
from datetime import datetime

from ..utils.memory_manager import MemoryManager
from ..api.models import JobSpec, JobOptions
from ..api.interfaces import Engine, EventSink


@dataclass
class DestinationProgress:
    """Track progress for individual destinations"""
    path: str
    transfer_type: str
    total_bytes: int = 0
    copied_bytes: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    current_speed_mbps: float = 0.0
    peak_speed_mbps: float = 0.0
    completed_files: int = 0
    total_files: int = 0
    is_complete: bool = False
    params: Dict[str, Any] = None
    
    @property
    def progress_percent(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return min(100.0, (self.copied_bytes / self.total_bytes) * 100.0)
    
    @property
    def elapsed_time(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    @property
    def average_speed_mbps(self) -> float:
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return (self.copied_bytes / (1024 * 1024)) / elapsed


@dataclass
class FileTransferTask:
    """Represents a file that needs to be transferred"""
    source_path: str
    filename: str
    size: int
    destinations: List[str]
    priority: int = 0  # Higher priority files transferred first


class EnhancedMultiDestinationEngine(Engine):
    """Enhanced engine that optimizes transfers for different destination types"""
    
    def __init__(self, sink: Optional[EventSink] = None):
        self.sink = sink
        self.memory_manager = MemoryManager()
        self.destination_progress: Dict[str, DestinationProgress] = {}
        self.cancelled = threading.Event()
        self.paused = threading.Event()
        self.job_start_time: Optional[float] = None
        self.total_bytes = 0
        self.total_files = 0
        self._memory_buffer_size = 0
        self._use_memory_buffering = True
        
        # Thread pool for parallel transfers
        self.max_workers = min(8, (os.cpu_count() or 4) * 2)
        self.executor: Optional[ThreadPoolExecutor] = None
        
        print(f"DEBUG: EnhancedMultiDestinationEngine initialized with max_workers={self.max_workers}")
    
    def start(self, job: JobSpec) -> None:
        """Start the enhanced multi-destination transfer"""
        print(f"DEBUG: Enhanced multi-destination transfer starting for job {job.job_id}")
        
        try:
            # Initialize progress tracking for each destination
            self._initialize_destinations(job)
            
            # Calculate memory requirements and strategy
            self._plan_memory_strategy(job)
            
            # Get list of files to transfer
            files = self._discover_files(job.source_root)
            self.total_files = len(files)
            self.total_bytes = sum(f.size for f in files)
            
            print(f"DEBUG: Found {self.total_files} files, {self.total_bytes / (1024*1024):.1f}MB total")
            
            # Emit job started event
            self._emit_job_started()
            
            # Execute transfer strategy
            if self._use_memory_buffering and self._can_fit_in_memory():
                print("DEBUG: Using memory-buffered multi-destination strategy")
                self._execute_memory_buffered_transfer(files, job)
            else:
                print("DEBUG: Using streaming multi-destination strategy")
                self._execute_streaming_transfer(files, job)
            
            # Complete the job
            self._emit_job_completed()
            
        except Exception as e:
            print(f"DEBUG: Error in enhanced transfer: {e}")
            import traceback
            traceback.print_exc()
            self._emit_job_error(str(e))
    
    def _initialize_destinations(self, job: JobSpec) -> None:
        """Initialize progress tracking and parameters for each destination"""
        for dest_path in job.destination_roots:
            # Get optimized parameters for this destination
            params = self.memory_manager.get_optimal_transfer_params_for_destination(dest_path)
            
            progress = DestinationProgress(
                path=dest_path,
                transfer_type=params['transfer_type'],
                params=params
            )
            
            self.destination_progress[dest_path] = progress
            print(f"DEBUG: Initialized destination {dest_path} with type {params['transfer_type']}")
    
    def _plan_memory_strategy(self, job: JobSpec) -> None:
        """Plan memory usage strategy based on available memory and file sizes"""
        available_memory = self.memory_manager.get_available_memory()
        memory_config = self.memory_manager.get_optimal_config()
        
        # Reserve memory for buffering (up to 50% of available memory)
        max_buffer_memory = available_memory * 0.5
        
        # Calculate if we can buffer files in memory
        source_size = self._estimate_source_size(job.source_root)
        
        if source_size < max_buffer_memory:
            self._memory_buffer_size = int(max_buffer_memory * 1024 * 1024)
            self._use_memory_buffering = True
            print(f"DEBUG: Memory buffering enabled - {max_buffer_memory:.1f}MB buffer for {source_size:.1f}MB data")
        else:
            self._use_memory_buffering = False
            print(f"DEBUG: Memory buffering disabled - {source_size:.1f}MB data > {max_buffer_memory:.1f}MB buffer")
    
    def _estimate_source_size(self, source_root: str) -> float:
        """Estimate total size of source data in MB"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(source_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        continue
            return total_size / (1024 * 1024)
        except Exception as e:
            print(f"DEBUG: Error estimating source size: {e}")
            return 1024.0  # Default to 1GB if we can't estimate
    
    def _can_fit_in_memory(self) -> bool:
        """Check if the current dataset can fit in available memory"""
        return self.total_bytes < self._memory_buffer_size
    
    def _discover_files(self, source_root: str) -> List[FileTransferTask]:
        """Discover all files to be transferred and create transfer tasks"""
        files = []
        
        try:
            for root, dirs, filenames in os.walk(source_root):
                for filename in filenames:
                    source_path = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(source_path)
                        
                        # Create transfer task
                        task = FileTransferTask(
                            source_path=source_path,
                            filename=filename,
                            size=size,
                            destinations=list(self.destination_progress.keys()),
                            priority=1  # Could be enhanced with file type prioritization
                        )
                        files.append(task)
                        
                    except OSError as e:
                        print(f"DEBUG: Skipping file {source_path}: {e}")
                        continue
            
            # Sort by priority (high priority first) then by size (large files first)
            files.sort(key=lambda f: (-f.priority, -f.size))
            
        except Exception as e:
            print(f"DEBUG: Error discovering files: {e}")
            raise
        
        return files
    
    def _execute_memory_buffered_transfer(self, files: List[FileTransferTask], job: JobSpec) -> None:
        """Execute transfer using memory buffering for optimal multi-destination performance"""
        print("DEBUG: Starting memory-buffered transfer strategy")
        
        # Sort destinations by priority (fastest first)
        destinations = sorted(
            self.destination_progress.keys(),
            key=lambda d: self.destination_progress[d].params.get('priority', 'normal'),
            reverse=True
        )
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            self.executor = executor
            
            for file_task in files:
                if self.cancelled.is_set():
                    break
                
                # Wait if paused
                while self.paused.is_set() and not self.cancelled.is_set():
                    time.sleep(0.1)
                
                # Load file into memory
                try:
                    print(f"DEBUG: Loading {file_task.filename} into memory...")
                    with open(file_task.source_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Start transfers to all destinations simultaneously
                    future_to_dest = {}
                    for dest_path in destinations:
                        future = executor.submit(
                            self._transfer_from_memory,
                            file_data,
                            file_task,
                            dest_path
                        )
                        future_to_dest[future] = dest_path
                    
                    # Wait for all destinations to complete
                    for future in as_completed(future_to_dest):
                        dest_path = future_to_dest[future]
                        try:
                            success = future.result()
                            if success:
                                self._update_destination_progress(dest_path, file_task.size)
                            print(f"DEBUG: {file_task.filename} -> {dest_path}: {'SUCCESS' if success else 'FAILED'}")
                        except Exception as e:
                            print(f"DEBUG: Transfer failed for {dest_path}: {e}")
                
                except Exception as e:
                    print(f"DEBUG: Failed to load {file_task.filename}: {e}")
                    continue
    
    def _execute_streaming_transfer(self, files: List[FileTransferTask], job: JobSpec) -> None:
        """Execute transfer using streaming for large datasets"""
        print("DEBUG: Starting streaming transfer strategy")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            self.executor = executor
            
            # Submit all file transfers
            futures = []
            for file_task in files:
                if self.cancelled.is_set():
                    break
                
                future = executor.submit(self._transfer_file_streaming, file_task)
                futures.append((future, file_task))
            
            # Process completed transfers
            for future, file_task in futures:
                if self.cancelled.is_set():
                    break
                
                try:
                    future.result()
                except Exception as e:
                    print(f"DEBUG: Streaming transfer failed for {file_task.filename}: {e}")
    
    def _transfer_from_memory(self, file_data: bytes, file_task: FileTransferTask, dest_path: str) -> bool:
        """Transfer file data from memory to a specific destination"""
        try:
            # Create destination directory structure
            rel_path = os.path.relpath(file_task.source_path, os.path.dirname(file_task.source_path))
            dest_file_path = os.path.join(dest_path, rel_path)
            dest_dir = os.path.dirname(dest_file_path)
            
            os.makedirs(dest_dir, exist_ok=True)
            
            # Get optimized parameters for this destination
            params = self.destination_progress[dest_path].params
            block_size = params.get('block_size', 4 * 1024 * 1024)
            
            # Write file with optimal block size
            start_time = time.time()
            with open(dest_file_path, 'wb') as f:
                bytes_written = 0
                for i in range(0, len(file_data), block_size):
                    if self.cancelled.is_set():
                        return False
                    
                    chunk = file_data[i:i + block_size]
                    f.write(chunk)
                    bytes_written += len(chunk)
                    
                    # Update speed calculation
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        speed_mbps = (bytes_written / (1024 * 1024)) / elapsed
                        self._update_destination_speed(dest_path, speed_mbps)
            
            # Verify file size
            if os.path.getsize(dest_file_path) == len(file_data):
                return True
            else:
                print(f"DEBUG: Size mismatch for {dest_file_path}")
                return False
            
        except Exception as e:
            print(f"DEBUG: Memory transfer failed: {e}")
            return False
    
    def _transfer_file_streaming(self, file_task: FileTransferTask) -> None:
        """Transfer a file using streaming to all destinations"""
        try:
            # Sort destinations by expected speed (fastest first)
            destinations = sorted(
                file_task.destinations,
                key=lambda d: self.destination_progress[d].params.get('expected_speed_mbps', 0),
                reverse=True
            )
            
            # Transfer to each destination
            for dest_path in destinations:
                if self.cancelled.is_set():
                    break
                
                # Wait if paused
                while self.paused.is_set() and not self.cancelled.is_set():
                    time.sleep(0.1)
                
                if self._transfer_file_to_destination(file_task, dest_path):
                    self._update_destination_progress(dest_path, file_task.size)
                
        except Exception as e:
            print(f"DEBUG: Streaming transfer failed: {e}")
            raise
    
    def _transfer_file_to_destination(self, file_task: FileTransferTask, dest_path: str) -> bool:
        """Transfer a single file to a destination with optimized parameters"""
        try:
            # Create destination path
            rel_path = os.path.relpath(file_task.source_path, os.path.dirname(file_task.source_path))
            dest_file_path = os.path.join(dest_path, rel_path)
            dest_dir = os.path.dirname(dest_file_path)
            
            os.makedirs(dest_dir, exist_ok=True)
            
            # Get optimized parameters
            params = self.destination_progress[dest_path].params
            block_size = params.get('block_size', 4 * 1024 * 1024)
            
            # Copy file with progress tracking
            start_time = time.time()
            bytes_copied = 0
            
            with open(file_task.source_path, 'rb') as src:
                with open(dest_file_path, 'wb') as dst:
                    while True:
                        if self.cancelled.is_set():
                            return False
                        
                        chunk = src.read(block_size)
                        if not chunk:
                            break
                        
                        dst.write(chunk)
                        bytes_copied += len(chunk)
                        
                        # Update speed
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            speed_mbps = (bytes_copied / (1024 * 1024)) / elapsed
                            self._update_destination_speed(dest_path, speed_mbps)
            
            return True
            
        except Exception as e:
            print(f"DEBUG: File transfer failed: {e}")
            return False
    
    def _update_destination_progress(self, dest_path: str, bytes_added: int) -> None:
        """Update progress for a specific destination"""
        progress = self.destination_progress[dest_path]
        progress.copied_bytes += bytes_added
        progress.completed_files += 1
        
        # Update totals for destination
        if progress.start_time is None:
            progress.start_time = time.time()
        
        # Emit destination-specific progress
        self._emit_destination_progress(dest_path)
        
        # Emit overall job progress
        self._emit_job_progress()
    
    def _update_destination_speed(self, dest_path: str, speed_mbps: float) -> None:
        """Update speed tracking for a destination"""
        progress = self.destination_progress[dest_path]
        progress.current_speed_mbps = speed_mbps
        progress.peak_speed_mbps = max(progress.peak_speed_mbps, speed_mbps)
    
    def _emit_job_started(self) -> None:
        """Emit job started event"""
        self.job_start_time = time.time()
        
        if self.sink:
            self.sink.emit("job.started", {
                "total_files": self.total_files,
                "total_bytes": self.total_bytes,
                "destinations": list(self.destination_progress.keys())
            })
    
    def _emit_job_progress(self) -> None:
        """Emit job progress event with aggregated progress"""
        total_copied = sum(p.copied_bytes for p in self.destination_progress.values())
        completed_files = sum(p.completed_files for p in self.destination_progress.values())
        
        if self.sink:
            elapsed = time.time() - self.job_start_time if self.job_start_time else 0
            speed_mbps = (total_copied / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            
            self.sink.emit("job.progress", {
                "copied_bytes": total_copied,
                "total_bytes": self.total_bytes * len(self.destination_progress),  # Total across all destinations
                "completed_files": completed_files,
                "total_files": self.total_files * len(self.destination_progress),
                "speed_mbps": speed_mbps,
                "elapsed_time": elapsed
            })
    
    def _emit_destination_progress(self, dest_path: str) -> None:
        """Emit progress event for a specific destination"""
        progress = self.destination_progress[dest_path]
        dest_index = list(self.destination_progress.keys()).index(dest_path)
        
        if self.sink:
            self.sink.emit("dest.progress", {
                "dest_index": dest_index,
                "dest_path": dest_path,
                "transfer_type": progress.transfer_type,
                "bytes_copied": progress.copied_bytes,
                "total_bytes": self.total_bytes,
                "completed_files": progress.completed_files,
                "total_files": self.total_files,
                "progress_percent": progress.progress_percent,
                "current_speed_mbps": progress.current_speed_mbps,
                "peak_speed_mbps": progress.peak_speed_mbps,
                "average_speed_mbps": progress.average_speed_mbps,
                "elapsed_time": progress.elapsed_time
            })
    
    def _emit_job_completed(self) -> None:
        """Emit job completed event"""
        if self.sink:
            total_copied = sum(p.copied_bytes for p in self.destination_progress.values())
            elapsed = time.time() - self.job_start_time if self.job_start_time else 0
            
            self.sink.emit("job.completed", {
                "copied_bytes": total_copied,
                "total_bytes": self.total_bytes * len(self.destination_progress),
                "elapsed": elapsed,
                "speed": (total_copied / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            })
    
    def _emit_job_error(self, error_message: str) -> None:
        """Emit job error event"""
        if self.sink:
            self.sink.emit("job.error", {"error": error_message})
    
    def cancel(self, job_id: str) -> None:
        """Cancel the transfer"""
        print(f"DEBUG: Cancelling enhanced multi-destination transfer {job_id}")
        self.cancelled.set()
        
        if self.executor:
            self.executor.shutdown(wait=False)
    
    def pause(self, job_id: str) -> None:
        """Pause the transfer"""
        print(f"DEBUG: Pausing enhanced multi-destination transfer {job_id}")
        self.paused.set()
    
    def resume(self, job_id: str) -> None:
        """Resume the transfer"""
        print(f"DEBUG: Resuming enhanced multi-destination transfer {job_id}")
        self.paused.clear()
