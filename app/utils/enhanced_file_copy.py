#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative
"""
Enhanced File Copy Engine

High-performance file copying with adaptive I/O, multi-threading, and integrity verification.
Designed to work seamlessly with PyInstaller packaging and existing app structure.
"""

import os
import sys
import shutil
import threading
import time
import hashlib
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import mmap
import fcntl
import struct

# Platform-specific imports
if platform.system() == "Windows":
    import win32file
    import win32api
    import win32con
    import pywintypes
elif platform.system() == "Darwin":  # macOS
    import fcntl
else:  # Linux
    import fcntl
    import posix_fallocate

# Optional imports for enhanced features
try:
    import xxhash
    XXHASH_AVAILABLE = True
except ImportError:
    XXHASH_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class CopyStats:
    """Statistics for copy operations"""
    total_files: int = 0
    copied_files: int = 0
    total_bytes: int = 0
    copied_bytes: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    speed_mbps: float = 0.0
    errors: List[str] = None
    hash_verifications: int = 0
    hash_failures: int = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def duration(self) -> float:
        """Duration of the copy operation in seconds"""
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        """Success rate as a percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.copied_files / self.total_files) * 100.0


@dataclass
class CopyOptions:
    """Configuration options for copy operations"""
    block_size: int = 1024 * 1024  # 1MB default
    thread_count: Optional[int] = None
    use_direct_io: bool = True
    verify_integrity: bool = True
    hash_algorithm: str = "xxhash64"  # xxhash64, sha256, md5
    progress_callback: Optional[Callable] = None
    cancel_event: Optional[threading.Event] = None
    pause_event: Optional[threading.Event] = None
    adaptive_parameters: bool = True
    large_file_threshold: int = 100 * 1024 * 1024  # 100MB


class CrossPlatformIO:
    """Cross-platform direct I/O operations"""
    
    @staticmethod
    def get_optimal_block_size() -> int:
        """Get optimal block size based on system"""
        if platform.system() == "Windows":
            return 64 * 1024  # 64KB for Windows
        else:
            return 1024 * 1024  # 1MB for Unix-like systems
    
    @staticmethod
    def get_optimal_thread_count() -> int:
        """Get optimal thread count based on CPU cores"""
        if PSUTIL_AVAILABLE:
            return min(psutil.cpu_count(logical=True) * 2, 32)
        else:
            # Fallback to basic detection
            try:
                return min(os.cpu_count() * 2, 32)
            except:
                return 8
    
    @staticmethod
    def open_direct_read(file_path: str) -> Any:
        """Open file for direct read (bypassing cache)"""
        try:
            if platform.system() == "Windows":
                handle = win32file.CreateFile(
                    file_path,
                    win32file.GENERIC_READ,
                    win32file.FILE_SHARE_READ,
                    None,
                    win32file.OPEN_EXISTING,
                    win32file.FILE_FLAG_NO_BUFFERING | win32file.FILE_FLAG_SEQUENTIAL_SCAN,
                    None
                )
                return handle
            elif platform.system() == "Darwin":  # macOS
                fd = os.open(file_path, os.O_RDONLY)
                fcntl.fcntl(fd, fcntl.F_NOCACHE, 1)
                return fd
            else:  # Linux
                fd = os.open(file_path, os.O_RDONLY | os.O_DIRECT)
                return fd
        except (OSError, IOError):
            # Fallback to regular file open
            return open(file_path, 'rb')
    
    @staticmethod
    def open_direct_write(file_path: str, file_size: int = 0) -> Any:
        """Open file for direct write (bypassing cache)"""
        try:
            if platform.system() == "Windows":
                handle = win32file.CreateFile(
                    file_path,
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.CREATE_ALWAYS,
                    win32file.FILE_FLAG_NO_BUFFERING | win32file.FILE_FLAG_SEQUENTIAL_SCAN,
                    None
                )
                if file_size > 0:
                    win32file.SetFilePointer(handle, file_size, win32file.FILE_BEGIN)
                    win32file.SetEndOfFile(handle)
                return handle
            elif platform.system() == "Darwin":  # macOS
                fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                fcntl.fcntl(fd, fcntl.F_NOCACHE, 1)
                if file_size > 0:
                    os.ftruncate(fd, file_size)
                return fd
            else:  # Linux
                fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_DIRECT, 0o644)
                if file_size > 0:
                    posix_fallocate(fd, 0, file_size)
                return fd
        except (OSError, IOError):
            # Fallback to regular file open
            return open(file_path, 'wb')
    
    @staticmethod
    def close_handle(handle: Any) -> None:
        """Close file handle"""
        try:
            if hasattr(handle, 'close'):
                handle.close()
            elif isinstance(handle, int):
                os.close(handle)
        except:
            pass
    
    @staticmethod
    def read_direct(handle: Any, size: int) -> bytes:
        """Read data using direct I/O"""
        try:
            if platform.system() == "Windows":
                return win32file.ReadFile(handle, size)[1]
            else:
                return os.read(handle, size)
        except:
            # Fallback to regular read
            return handle.read(size)
    
    @staticmethod
    def write_direct(handle: Any, data: bytes) -> int:
        """Write data using direct I/O"""
        try:
            if platform.system() == "Windows":
                win32file.WriteFile(handle, data)
                return len(data)
            else:
                return os.write(handle, data)
        except:
            # Fallback to regular write
            return handle.write(data)


class HashCalculator:
    """Calculate file hashes for integrity verification"""
    
    @staticmethod
    def calculate_hash(data: bytes, algorithm: str = "xxhash64") -> str:
        """Calculate hash of data"""
        if algorithm == "xxhash64" and XXHASH_AVAILABLE:
            return xxhash.xxh64(data).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(data).hexdigest()
        else:
            # Fallback to xxhash if available, otherwise sha256
            if XXHASH_AVAILABLE:
                return xxhash.xxh64(data).hexdigest()
            else:
                return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "xxhash64", 
                           block_size: int = 1024 * 1024) -> str:
        """Calculate hash of entire file"""
        if algorithm == "xxhash64" and XXHASH_AVAILABLE:
            hasher = xxhash.xxh64()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "md5":
            hasher = hashlib.md5()
        else:
            if XXHASH_AVAILABLE:
                hasher = xxhash.xxh64()
            else:
                hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                hasher.update(data)
        
        return hasher.hexdigest()


class BandwidthDetector:
    """Detect system bandwidth for adaptive parameter tuning"""
    
    @staticmethod
    def test_disk_bandwidth(test_dir: str = None) -> float:
        """Test disk bandwidth in MB/s"""
        if test_dir is None:
            test_dir = tempfile.gettempdir()
        
        test_file = os.path.join(test_dir, f"bandwidth_test_{int(time.time())}.tmp")
        test_size = 100 * 1024 * 1024  # 100MB test
        
        try:
            # Write test
            start_time = time.time()
            with open(test_file, 'wb') as f:
                f.write(b'0' * test_size)
            write_time = time.time() - start_time
            
            # Read test
            start_time = time.time()
            with open(test_file, 'rb') as f:
                f.read()
            read_time = time.time() - start_time
            
            # Calculate bandwidth (average of read/write)
            write_speed = test_size / (1024 * 1024) / write_time
            read_speed = test_size / (1024 * 1024) / read_time
            avg_speed = (write_speed + read_speed) / 2
            
            return avg_speed
        except:
            return 100.0  # Default fallback
        finally:
            try:
                os.remove(test_file)
            except:
                pass
    
    @staticmethod
    def get_optimal_parameters(bandwidth_mbps: float = None) -> Dict[str, Any]:
        """Get optimal parameters based on bandwidth"""
        if bandwidth_mbps is None:
            bandwidth_mbps = BandwidthDetector.test_disk_bandwidth()
        
        # Adaptive parameters based on bandwidth
        if bandwidth_mbps > 1000:  # High-speed storage
            block_size = 2 * 1024 * 1024  # 2MB
            thread_count = min(16, CrossPlatformIO.get_optimal_thread_count())
        elif bandwidth_mbps > 100:  # SSD
            block_size = 1024 * 1024  # 1MB
            thread_count = min(8, CrossPlatformIO.get_optimal_thread_count())
        else:  # HDD or network
            block_size = 512 * 1024  # 512KB
            thread_count = min(4, CrossPlatformIO.get_optimal_thread_count())
        
        return {
            'block_size': block_size,
            'thread_count': thread_count,
            'use_direct_io': bandwidth_mbps > 50,  # Use direct I/O for faster storage
            'large_file_threshold': 50 * 1024 * 1024 if bandwidth_mbps > 100 else 100 * 1024 * 1024
        }


class EnhancedFileCopy:
    """Enhanced file copy engine with adaptive I/O and multi-threading"""
    
    def __init__(self):
        self.stats = CopyStats()
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
    
    def copy_files(self, source_paths: List[str], destination_paths: List[str], 
                   options: Optional[CopyOptions] = None) -> CopyStats:
        """Copy files with enhanced performance features"""
        if options is None:
            options = CopyOptions()
        
        # Apply adaptive parameters if enabled
        if options.adaptive_parameters:
            bandwidth = BandwidthDetector.test_disk_bandwidth()
            optimal_params = BandwidthDetector.get_optimal_parameters(bandwidth)
            
            if options.block_size is None:
                options.block_size = optimal_params['block_size']
            if options.thread_count is None:
                options.thread_count = optimal_params['thread_count']
            if options.use_direct_io is None:
                options.use_direct_io = optimal_params['use_direct_io']
            if options.large_file_threshold is None:
                options.large_file_threshold = optimal_params['large_file_threshold']
        
        # Set default thread count if not specified
        if options.thread_count is None:
            options.thread_count = CrossPlatformIO.get_optimal_thread_count()
        
        # Set default block size if not specified
        if options.block_size is None:
            options.block_size = CrossPlatformIO.get_optimal_block_size()
        
        # Initialize stats
        self.stats = CopyStats()
        self.stats.start_time = time.time()
        
        # Set cancel/pause events
        self._cancel_event = options.cancel_event or threading.Event()
        self._pause_event = options.pause_event or threading.Event()
        
        try:
            # Collect all files to copy
            all_files = self._collect_files(source_paths)
            self.stats.total_files = len(all_files)
            self.stats.total_bytes = sum(os.path.getsize(f) for f in all_files)
            
            # Handle multiple destinations
            if len(destination_paths) > 1:
                self._copy_to_multiple_destinations(all_files, destination_paths, options)
            else:
                self._copy_to_single_destination(all_files, destination_paths[0], options)
        
        except Exception as e:
            self.stats.errors.append(str(e))
        finally:
            self.stats.end_time = time.time()
            if self.stats.duration > 0:
                self.stats.speed_mbps = (self.stats.copied_bytes / (1024 * 1024)) / self.stats.duration
        
        return self.stats
    
    def _collect_files(self, source_paths: List[str]) -> List[str]:
        """Collect all files to be copied"""
        files = []
        for source_path in source_paths:
            if os.path.isfile(source_path):
                files.append(source_path)
            elif os.path.isdir(source_path):
                for root, dirs, filenames in os.walk(source_path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
        return files
    
    def _copy_to_single_destination(self, source_files: List[str], destination: str, options: CopyOptions):
        """Copy files to a single destination"""
        os.makedirs(destination, exist_ok=True)
        
        with ThreadPoolExecutor(max_workers=options.thread_count) as executor:
            futures = []
            for source_file in source_files:
                if self._cancel_event.is_set():
                    break
                
                # Calculate destination path
                rel_path = os.path.relpath(source_file, os.path.commonpath(source_files))
                dest_file = os.path.join(destination, rel_path)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                
                # Submit copy task
                future = executor.submit(self._copy_single_file, source_file, dest_file, options)
                futures.append(future)
            
            # Wait for completion
            for future in as_completed(futures):
                if self._cancel_event.is_set():
                    break
                
                try:
                    success = future.result()
                    if success:
                        self.stats.copied_files += 1
                except Exception as e:
                    self.stats.errors.append(str(e))
    
    def _copy_to_multiple_destinations(self, source_files: List[str], destinations: List[str], options: CopyOptions):
        """Copy files to multiple destinations concurrently"""
        # Create destination directories
        for dest in destinations:
            os.makedirs(dest, exist_ok=True)
        
        # Use separate thread pools for each destination
        with ThreadPoolExecutor(max_workers=len(destinations) * options.thread_count) as executor:
            futures = []
            
            for source_file in source_files:
                if self._cancel_event.is_set():
                    break
                
                # Submit copy task for each destination
                for destination in destinations:
                    rel_path = os.path.relpath(source_file, os.path.commonpath(source_files))
                    dest_file = os.path.join(destination, rel_path)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    
                    future = executor.submit(self._copy_single_file, source_file, dest_file, options)
                    futures.append(future)
            
            # Wait for completion
            for future in as_completed(futures):
                if self._cancel_event.is_set():
                    break
                
                try:
                    success = future.result()
                    if success:
                        self.stats.copied_files += 1
                except Exception as e:
                    self.stats.errors.append(str(e))
    
    def _copy_single_file(self, source_path: str, dest_path: str, options: CopyOptions) -> bool:
        """Copy a single file with enhanced features"""
        try:
            file_size = os.path.getsize(source_path)
            
            # Choose copy method based on file size
            if file_size > options.large_file_threshold:
                return self._copy_large_file(source_path, dest_path, options)
            else:
                return self._copy_small_file(source_path, dest_path, options)
        
        except Exception as e:
            self.stats.errors.append(f"Error copying {source_path}: {e}")
            return False
    
    def _copy_large_file(self, source_path: str, dest_path: str, options: CopyOptions) -> bool:
        """Copy large file using multi-threaded range copying"""
        try:
            file_size = os.path.getsize(source_path)
            
            # Split file into ranges for parallel copying
            ranges = self._split_file_ranges(file_size, options.thread_count)
            
            # Create temporary file for assembly
            temp_file = dest_path + ".tmp"
            
            with ThreadPoolExecutor(max_workers=options.thread_count) as executor:
                futures = []
                
                for start, end in ranges:
                    if self._cancel_event.is_set():
                        break
                    
                    future = executor.submit(self._copy_file_range, source_path, temp_file, start, end, options)
                    futures.append(future)
                
                # Wait for all ranges to complete
                for future in as_completed(futures):
                    if self._cancel_event.is_set():
                        break
                    
                    if not future.result():
                        return False
            
            # Verify integrity if requested
            if options.verify_integrity:
                if not self._verify_file_integrity(source_path, temp_file, options.hash_algorithm):
                    self.stats.hash_failures += 1
                    return False
                self.stats.hash_verifications += 1
            
            # Move temporary file to final destination
            shutil.move(temp_file, dest_path)
            
            self.stats.copied_bytes += file_size
            return True
        
        except Exception as e:
            self.stats.errors.append(f"Error copying large file {source_path}: {e}")
            return False
    
    def _copy_small_file(self, source_path: str, dest_path: str, options: CopyOptions) -> bool:
        """Copy small file using direct I/O or buffered I/O"""
        try:
            file_size = os.path.getsize(source_path)
            
            if options.use_direct_io:
                return self._copy_with_direct_io(source_path, dest_path, options)
            else:
                return self._copy_with_buffered_io(source_path, dest_path, options)
        
        except Exception as e:
            self.stats.errors.append(f"Error copying small file {source_path}: {e}")
            return False
    
    def _copy_with_direct_io(self, source_path: str, dest_path: str, options: CopyOptions) -> bool:
        """Copy file using direct I/O"""
        try:
            file_size = os.path.getsize(source_path)
            
            # Open files with direct I/O
            src_handle = CrossPlatformIO.open_direct_read(source_path)
            dst_handle = CrossPlatformIO.open_direct_write(dest_path, file_size)
            
            try:
                copied_bytes = 0
                while copied_bytes < file_size:
                    if self._cancel_event.is_set():
                        return False
                    
                    # Wait if paused
                    while self._pause_event.is_set():
                        time.sleep(0.1)
                    
                    # Calculate read size
                    remaining = file_size - copied_bytes
                    read_size = min(options.block_size, remaining)
                    
                    # Read and write data
                    data = CrossPlatformIO.read_direct(src_handle, read_size)
                    if not data:
                        break
                    
                    CrossPlatformIO.write_direct(dst_handle, data)
                    copied_bytes += len(data)
                    
                    # Update progress
                    self.stats.copied_bytes += len(data)
                    if options.progress_callback:
                        options.progress_callback(copied_bytes, file_size)
                
                return copied_bytes == file_size
            
            finally:
                CrossPlatformIO.close_handle(src_handle)
                CrossPlatformIO.close_handle(dst_handle)
        
        except Exception as e:
            self.stats.errors.append(f"Error in direct I/O copy: {e}")
            return False
    
    def _copy_with_buffered_io(self, source_path: str, dest_path: str, options: CopyOptions) -> bool:
        """Copy file using buffered I/O"""
        try:
            with open(source_path, 'rb') as src, open(dest_path, 'wb') as dst:
                copied_bytes = 0
                file_size = os.path.getsize(source_path)
                
                while True:
                    if self._cancel_event.is_set():
                        return False
                    
                    # Wait if paused
                    while self._pause_event.is_set():
                        time.sleep(0.1)
                    
                    data = src.read(options.block_size)
                    if not data:
                        break
                    
                    dst.write(data)
                    copied_bytes += len(data)
                    
                    # Update progress
                    self.stats.copied_bytes += len(data)
                    if options.progress_callback:
                        options.progress_callback(copied_bytes, file_size)
                
                return copied_bytes == file_size
        
        except Exception as e:
            self.stats.errors.append(f"Error in buffered I/O copy: {e}")
            return False
    
    def _copy_file_range(self, source_path: str, dest_path: str, start: int, end: int, options: CopyOptions) -> bool:
        """Copy a specific range of a file"""
        try:
            range_size = end - start
            
            if options.use_direct_io:
                return self._copy_range_with_direct_io(source_path, dest_path, start, end, options)
            else:
                return self._copy_range_with_buffered_io(source_path, dest_path, start, end, options)
        
        except Exception as e:
            self.stats.errors.append(f"Error copying range {start}-{end}: {e}")
            return False
    
    def _copy_range_with_direct_io(self, source_path: str, dest_path: str, start: int, end: int, options: CopyOptions) -> bool:
        """Copy range using direct I/O"""
        try:
            src_handle = CrossPlatformIO.open_direct_read(source_path)
            dst_handle = CrossPlatformIO.open_direct_write(dest_path)
            
            try:
                # Seek to start position
                if platform.system() == "Windows":
                    win32file.SetFilePointer(src_handle, start, win32file.FILE_BEGIN)
                    win32file.SetFilePointer(dst_handle, start, win32file.FILE_BEGIN)
                else:
                    os.lseek(src_handle, start, os.SEEK_SET)
                    os.lseek(dst_handle, start, os.SEEK_SET)
                
                copied_bytes = 0
                range_size = end - start
                
                while copied_bytes < range_size:
                    if self._cancel_event.is_set():
                        return False
                    
                    remaining = range_size - copied_bytes
                    read_size = min(options.block_size, remaining)
                    
                    data = CrossPlatformIO.read_direct(src_handle, read_size)
                    if not data:
                        break
                    
                    CrossPlatformIO.write_direct(dst_handle, data)
                    copied_bytes += len(data)
                
                return copied_bytes == range_size
            
            finally:
                CrossPlatformIO.close_handle(src_handle)
                CrossPlatformIO.close_handle(dst_handle)
        
        except Exception as e:
            self.stats.errors.append(f"Error in direct I/O range copy: {e}")
            return False
    
    def _copy_range_with_buffered_io(self, source_path: str, dest_path: str, start: int, end: int, options: CopyOptions) -> bool:
        """Copy range using buffered I/O"""
        try:
            with open(source_path, 'rb') as src, open(dest_path, 'r+b') as dst:
                src.seek(start)
                dst.seek(start)
                
                copied_bytes = 0
                range_size = end - start
                
                while copied_bytes < range_size:
                    if self._cancel_event.is_set():
                        return False
                    
                    remaining = range_size - copied_bytes
                    read_size = min(options.block_size, remaining)
                    
                    data = src.read(read_size)
                    if not data:
                        break
                    
                    dst.write(data)
                    copied_bytes += len(data)
                
                return copied_bytes == range_size
        
        except Exception as e:
            self.stats.errors.append(f"Error in buffered I/O range copy: {e}")
            return False
    
    def _split_file_ranges(self, file_size: int, thread_count: int) -> List[Tuple[int, int]]:
        """Split file into ranges for parallel copying"""
        ranges = []
        chunk_size = file_size // thread_count
        
        for i in range(thread_count):
            start = i * chunk_size
            if i == thread_count - 1:
                end = file_size
            else:
                end = (i + 1) * chunk_size
            ranges.append((start, end))
        
        return ranges
    
    def _verify_file_integrity(self, source_path: str, dest_path: str, algorithm: str) -> bool:
        """Verify file integrity by comparing hashes"""
        try:
            source_hash = HashCalculator.calculate_file_hash(source_path, algorithm)
            dest_hash = HashCalculator.calculate_file_hash(dest_path, algorithm)
            return source_hash == dest_hash
        except Exception as e:
            self.stats.errors.append(f"Error verifying integrity: {e}")
            return False
    
    def cancel(self):
        """Cancel ongoing copy operations"""
        self._cancel_event.set()
    
    def pause(self):
        """Pause ongoing copy operations"""
        self._pause_event.set()
    
    def resume(self):
        """Resume paused copy operations"""
        self._pause_event.clear()


# Convenience functions for easy integration
def copy_files(source_paths: List[str], destination_paths: List[str], **kwargs) -> CopyStats:
    """Convenience function for copying files"""
    options = CopyOptions(**kwargs)
    copier = EnhancedFileCopy()
    return copier.copy_files(source_paths, destination_paths, options)


def copy_file(source_path: str, destination_path: str, **kwargs) -> CopyStats:
    """Convenience function for copying a single file"""
    return copy_files([source_path], [destination_path], **kwargs)


def copy_directory(source_dir: str, destination_dir: str, **kwargs) -> CopyStats:
    """Convenience function for copying a directory"""
    return copy_files([source_dir], [destination_dir], **kwargs)


# Integration with existing file operations
class EnhancedFileOperationsHandler:
    """Enhanced file operations handler that integrates with existing app structure"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.copier = EnhancedFileCopy()
    
    def import_file_enhanced(self, target_dir: str, file_path: str = None, 
                           show_dialog: bool = True, **copy_options) -> Tuple[bool, str]:
        """Enhanced file import with high-performance copying"""
        try:
            # Use existing dialog logic if needed
            if not file_path and show_dialog:
                from PyQt6.QtWidgets import QFileDialog
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent,
                    "Import File",
                    "",
                    "All Files (*)"
                )
                
                if not file_path:
                    return False, None
            
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            # Get the file name
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_dir, file_name)
            
            # Use enhanced copy
            options = CopyOptions(**copy_options)
            stats = self.copier.copy_files([file_path], [target_path], options)
            
            if stats.copied_files > 0:
                return True, target_path
            else:
                return False, None
        
        except Exception as e:
            if self.parent:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to import file: {e}"
                )
            return False, None
