#!/usr/bin/env python3
"""
C++ Enhanced Copy Engine Wrapper

This module provides a Python interface to the C++ enhanced high-performance
file copying engine for maximum performance.
"""

import os
import sys
import time
import platform
from typing import List, Optional, Dict, Any, Callable, Union
from dataclasses import dataclass
from pathlib import Path

# Try to import the C++ enhanced copy engine
CPP_ENGINE_AVAILABLE = False
cpp_engine = None

try:
    # Add the forwardflow engines path to sys.path
    import sys
    import os
    
    # Get the project root (assuming this file is in app/utils/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    # Ensure we're in the right project directory
    if os.path.basename(project_root) != 'FF_V1_1':
        project_root = os.path.join(project_root, 'FF_V1_1')
    forwardflow_path = os.path.join(project_root, 'forwardflow', 'ingest', 'engines')
    
    if forwardflow_path not in sys.path:
        sys.path.insert(0, forwardflow_path)
    
    try:
        # Use the working C++ engine from High_perf directory
        high_perf_path = os.path.join(forwardflow_path, "ingest", "engines", "High_perf")
        if high_perf_path not in sys.path:
            sys.path.insert(0, high_perf_path)
        
        import enhanced_high_perf_engine as cpp_engine
        CPP_ENGINE_AVAILABLE = True
        print("DEBUG: C++ engine imported successfully from High_perf directory")
    except ImportError as e:
        print(f"DEBUG: C++ engine import failed: {e}")
        CPP_ENGINE_AVAILABLE = False
        cpp_engine = None
        
except Exception as e:
    CPP_ENGINE_AVAILABLE = False
    cpp_engine = None
    print(f"Warning: C++ enhanced copy engine not available: {e}")

@dataclass
class CopyStats:
    """Statistics from copy operations"""
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
    
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def success_rate(self) -> float:
        return (self.copied_files * 100.0) / self.total_files if self.total_files > 0 else 0.0

@dataclass
class CopyOptions:
    """Options for copy operations with safer defaults"""
    block_size: int = 4 * 1024 * 1024  # 4MB default (safer)
    thread_count: int = 0  # 0 = auto-detect
    use_direct_io: Union[bool, str] = "auto"  # "auto", True, or False
    verify_integrity: bool = False  # FAST by default; user can enable
    hash_algorithm: str = "xxhash64"
    mtu_size: int = 1500  # Network MTU size
    socket_buffer_size: int = 1024 * 1024  # 1MB socket buffer
    adaptive_parameters: bool = True  # Auto-tune based on paths
    large_file_threshold: int = 100 * 1024 * 1024  # 100MB
    progress_callback: Optional[Callable] = None

class PathAnalyzer:
    """Analyzes file paths to determine optimal copy parameters"""
    
    @staticmethod
    def is_usb_or_thunderbolt(path: str) -> bool:
        """Check if path is on USB or Thunderbolt device"""
        try:
            path_obj = Path(path)
            if platform.system() == "Darwin":  # macOS
                # Check for /Volumes/ which typically indicates external drives
                if "/Volumes/" in str(path_obj.absolute()):
                    return True
                # Check for USB/Thunderbolt device paths
                if any(part.startswith("USB") or part.startswith("Thunderbolt") 
                      for part in path_obj.parts):
                    return True
            elif platform.system() == "Windows":
                # Windows USB drive detection
                if len(path) >= 2 and path[1] == ":":
                    drive = path[0].upper()
                    # This is a simplified check - in practice you'd use WMI
                    return False  # Assume not USB for now
            return False
        except Exception:
            return False
    
    @staticmethod
    def is_network_path(path: str) -> bool:
        """Check if path is a network location"""
        try:
            path_obj = Path(path)
            # Check for common network path patterns
            if platform.system() == "Darwin":  # macOS
                return any(part.startswith("smb://") or part.startswith("afp://") 
                          for part in path_obj.parts)
            elif platform.system() == "Windows":
                return path.startswith("\\\\") or ":" in path and "\\" in path
            return False
        except Exception:
            return False
    
    @staticmethod
    def is_nvme_path(path: str) -> bool:
        """Check if path is on NVMe storage"""
        try:
            path_obj = Path(path)
            if platform.system() == "Darwin":  # macOS
                # Check for NVMe device paths
                if any("nvme" in part.lower() for part in path_obj.parts):
                    return True
                # Check for SSD paths (simplified)
                return False
            elif platform.system() == "Windows":
                # Windows NVMe detection would require WMI queries
                return False
            return False
        except Exception:
            return False

class CppEnhancedCopyEngine:
    """C++ Enhanced Copy Engine - C++ ONLY, NO PYTHON FALLBACK"""
    
    def __init__(self):
        self.cpp_engine = cpp_engine if CPP_ENGINE_AVAILABLE else None
        if not self.cpp_engine:
            raise RuntimeError("C++ engine not available - this is the only engine")
    
    def _auto_tune_parameters(self, source_paths: List[str], destination_paths: List[str], 
                             options: CopyOptions) -> CopyOptions:
        """Auto-tune parameters based on path analysis"""
        tuned_options = CopyOptions()
        
        # Copy basic attributes
        if hasattr(options, 'block_size'):
            tuned_options.block_size = options.block_size
        if hasattr(options, 'thread_count'):
            tuned_options.thread_count = options.thread_count
        if hasattr(options, 'use_direct_io'):
            tuned_options.use_direct_io = options.use_direct_io
        if hasattr(options, 'verify_integrity'):
            tuned_options.verify_integrity = options.verify_integrity
        if hasattr(options, 'hash_algorithm'):
            tuned_options.hash_algorithm = options.hash_algorithm
        if hasattr(options, 'adaptive_parameters'):
            tuned_options.adaptive_parameters = options.adaptive_parameters
        if hasattr(options, 'large_file_threshold'):
            tuned_options.large_file_threshold = options.large_file_threshold
        if hasattr(options, 'progress_callback'):
            tuned_options.progress_callback = options.progress_callback
        
        # Analyze paths to determine optimal settings
        all_paths = source_paths + destination_paths
        
        # Check for USB/Thunderbolt
        has_usb_tb = any(PathAnalyzer.is_usb_or_thunderbolt(path) for path in all_paths)
        
        # Check for network paths
        has_network = any(PathAnalyzer.is_network_path(path) for path in all_paths)
        
        # Check for NVMe paths
        has_nvme = any(PathAnalyzer.is_nvme_path(path) for path in all_paths)
        
        # Auto-tune direct I/O
        if options.use_direct_io == "auto":
            if has_usb_tb:
                tuned_options.use_direct_io = False  # Buffered for USB/TB
            elif has_network or (has_nvme and len(all_paths) >= 2 and all(PathAnalyzer.is_nvme_path(p) for p in all_paths)):
                tuned_options.use_direct_io = True   # Direct for network/NVMe↔NVMe
            else:
                tuned_options.use_direct_io = False  # Default to buffered
        
        # Auto-tune block size
        if options.block_size == 4 * 1024 * 1024:  # Default value
            if has_usb_tb:
                tuned_options.block_size = 4 * 1024 * 1024  # 4MB for USB/TB
            elif has_network:
                tuned_options.block_size = 1 * 1024 * 1024  # 1MB for network
            elif has_nvme:
                tuned_options.block_size = 4 * 1024 * 1024  # 4MB for NVMe
            else:
                tuned_options.block_size = 4 * 1024 * 1024  # 4MB default
        
        # Auto-tune thread count
        if options.thread_count == 0:  # Auto-detect
            if has_usb_tb:
                tuned_options.thread_count = 1  # Single thread for USB/TB
            elif has_network:
                tuned_options.thread_count = 4  # Multiple threads for network
            elif has_nvme:
                tuned_options.thread_count = 2  # Moderate threading for NVMe
            else:
                tuned_options.thread_count = 2  # Default moderate threading
        
        return tuned_options
    
    def copy_files(self, source_paths: List[str], destination_paths: List[str], 
                   options: Optional[CopyOptions] = None) -> CopyStats:
        """
        Copy files using C++ engine ONLY - NO FALLBACK
        
        Args:
            source_paths: List of source file/directory paths
            destination_paths: List of destination paths
            options: Copy options
            
        Returns:
            CopyStats: Statistics from the copy operation
        """
        if options is None:
            options = CopyOptions()
        
        # Auto-tune parameters based on paths
        if options.adaptive_parameters:
            options = self._auto_tune_parameters(source_paths, destination_paths, options)
        
        # C++ ENGINE ONLY - NO FALLBACK
        if not self.cpp_engine:
            stats = CopyStats()
            stats.errors.append("C++ engine not available - this is the only engine")
            return stats
        
        print("DEBUG: Using C++ engine exclusively - no fallback")
        return self._copy_with_cpp_engine(source_paths, destination_paths, options)
    
    def _copy_with_cpp_engine(self, source_paths: List[str], destination_paths: List[str], 
                             options: CopyOptions) -> CopyStats:
        """Copy using C++ engine ONLY"""
        try:
            # Convert to C++ job
            cpp_job = cpp_engine.CopyJob()
            cpp_job.source_paths = source_paths
            cpp_job.destination_paths = destination_paths
            
            # Only set attributes that exist in the options
            if hasattr(options, 'block_size'):
                cpp_job.block_size = options.block_size
            if hasattr(options, 'thread_count'):
                cpp_job.thread_count = options.thread_count
            if hasattr(options, 'use_direct_io'):
                cpp_job.use_direct_io = bool(options.use_direct_io)  # Convert to bool
            if hasattr(options, 'verify_integrity'):
                cpp_job.verify_integrity = options.verify_integrity
            if hasattr(options, 'hash_algorithm'):
                cpp_job.hash_algorithm = options.hash_algorithm
            if hasattr(options, 'mtu_size'):
                cpp_job.mtu_size = options.mtu_size
            if hasattr(options, 'socket_buffer_size'):
                cpp_job.socket_buffer_size = options.socket_buffer_size
            if hasattr(options, 'adaptive_parameters'):
                cpp_job.adaptive_parameters = options.adaptive_parameters
            if hasattr(options, 'large_file_threshold'):
                cpp_job.large_file_threshold = options.large_file_threshold
            
            # Set up progress callback if provided
            if options.progress_callback:
                def cpp_progress_callback(event_type: str, payload: Dict[str, Any]):
                    options.progress_callback(event_type, payload)
                cpp_job.progress_callback = cpp_progress_callback
            
            # Perform copy
            cpp_stats = self.cpp_engine.copy_files(cpp_job)
            
            # Convert to Python stats
            stats = CopyStats(
                total_files=cpp_stats.total_files,
                copied_files=cpp_stats.copied_files,
                total_bytes=cpp_stats.total_bytes,
                copied_bytes=cpp_stats.copied_bytes,
                start_time=cpp_stats.start_time,
                end_time=cpp_stats.end_time,
                speed_mbps=cpp_stats.speed_mbps,
                errors=cpp_stats.errors,
                hash_verifications=cpp_stats.hash_verifications,
                hash_failures=cpp_stats.hash_failures
            )
            
            return stats
            
        except Exception as e:
            print(f"C++ engine failed: {e}")
            # NO FALLBACK - C++ ENGINE ONLY
            stats = CopyStats()
            stats.errors.append(f"C++ engine failed: {e}")
            return stats

# Global functions for backward compatibility
def copy_files(source_paths: List[str], destination_paths: List[str], 
               options: Optional[CopyOptions] = None) -> CopyStats:
    """Copy files using C++ engine only"""
    engine = CppEnhancedCopyEngine()
    return engine.copy_files(source_paths, destination_paths, options)

def copy_file(source_path: str, destination_path: str, 
              options: Optional[CopyOptions] = None) -> CopyStats:
    """Copy a single file using C++ engine only"""
    return copy_files([source_path], [destination_path], options)

def copy_directory(source_dir: str, destination_dir: str, 
                   options: Optional[CopyOptions] = None) -> CopyStats:
    """Copy a directory using C++ engine only"""
    # This would need to be implemented to scan the directory first
    # For now, just return an error
    stats = CopyStats()
    stats.errors.append("Directory copy not implemented - use copy_files with file lists")
    return stats
