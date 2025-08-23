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
    print(f"Warning: C++ enhanced copy engine not available, falling back to Python implementation: {e}")

# Import the Python fallback
try:
    from app.utils.enhanced_file_copy import (
        CopyStats as PyCopyStats, 
        CopyOptions as PyCopyOptions,
        EnhancedFileCopy as PyEnhancedFileCopy
    )
    PY_ENGINE_AVAILABLE = True
except ImportError:
    PY_ENGINE_AVAILABLE = False
    print("Warning: Python enhanced copy engine not available")

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
    mtu_size: int = 0  # 0 = auto-detect
    socket_buffer_size: int = 0  # 0 = auto-detect
    adaptive_parameters: bool = True
    large_file_threshold: int = 256 * 1024 * 1024  # 256MB (safer)
    progress_callback: Optional[Callable] = None
    # NEW: Separate concurrency knobs
    files_in_flight: int = 1  # files copying at once (1 for USB/TB, 2+ for networks/NVMe)
    ranges_per_file: int = 1  # parallel ranges inside one file (1 for USB/TB, 2+ for fast media)

class PathAnalyzer:
    """Analyze paths to determine optimal copy parameters"""
    
    @staticmethod
    def is_usb_or_thunderbolt(path: str) -> bool:
        """Detect if path is on USB or Thunderbolt device"""
        try:
            if platform.system() == "Darwin":  # macOS
                # Check if path contains /Volumes/ (external drives)
                if "/Volumes/" in path:
                    return True
                # Could add more sophisticated detection here
            elif platform.system() == "Windows":
                # Check for removable drives (D:, E:, etc.)
                if len(path) >= 2 and path[1] == ':' and path[0] in 'DEFGHIJKLMNOPQRSTUVWXYZ':
                    # This is a simple heuristic - could be improved
                    return True
            # Linux: could check /proc/mounts for USB devices
            return False
        except:
            return False
    
    @staticmethod
    def is_network_path(path: str) -> bool:
        """Detect if path is a network location"""
        try:
            # Common network path patterns
            network_patterns = [
                "//", "\\\\",  # SMB/CIFS
                "smb://", "nfs://", "ftp://", "sftp://",  # Various protocols
                "/mnt/", "/media/",  # Linux mount points
            ]
            
            path_lower = path.lower()
            return any(pattern in path_lower for pattern in network_patterns)
        except:
            return False
    
    @staticmethod
    def is_nvme_path(path: str) -> bool:
        """Detect if path is on NVMe storage (heuristic)"""
        try:
            if platform.system() == "Darwin":  # macOS
                # Check for common NVMe mount points
                nvme_patterns = ["/System/", "/Applications/", "/Users/"]
                return any(pattern in path for pattern in nvme_patterns)
            elif platform.system() == "Windows":
                # Usually C: drive on modern systems
                return path.startswith("C:")
            else:  # Linux
                # Check for /dev/nvme devices
                return "/dev/nvme" in path or "/nvme" in path
        except:
            return False

class CppEnhancedCopyEngine:
    """C++ Enhanced Copy Engine with Python fallback"""
    
    def __init__(self):
        self.cpp_engine = None
        self.py_engine = None
        
        # Check if C++ engine is available
        cpp_available = globals().get('CPP_ENGINE_AVAILABLE', False)
        py_available = globals().get('PY_ENGINE_AVAILABLE', False)
        
        if cpp_available:
            try:
                self.cpp_engine = cpp_engine.EnhancedHighPerfTransferEngine()
                print("✓ C++ Enhanced Copy Engine loaded successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize C++ engine: {e}")
                cpp_available = False
        
        if not cpp_available and py_available:
            try:
                self.py_engine = PyEnhancedFileCopy()
                print("✓ Using Python Enhanced Copy Engine as fallback")
            except Exception as e:
                print(f"Warning: Failed to initialize Python engine: {e}")
                py_available = False
        
        if not cpp_available and not py_available:
            print("Warning: No enhanced copy engines available")
    
    def _auto_tune_parameters(self, source_paths: List[str], destination_paths: List[str], 
                             options: CopyOptions) -> CopyOptions:
        """Auto-tune parameters based on source and destination paths"""
        # Only copy attributes that exist in the target CopyOptions class
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
        Copy files using the best available engine with auto-tuning
        
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
        
        if self.cpp_engine:
            return self._copy_with_cpp_engine(source_paths, destination_paths, options)
        elif self.py_engine:
            return self._copy_with_py_engine(source_paths, destination_paths, options)
        else:
            # No engines available, return error stats
            stats = CopyStats()
            stats.errors.append("No enhanced copy engines available")
            return stats
    
    def _copy_with_cpp_engine(self, source_paths: List[str], destination_paths: List[str], 
                             options: CopyOptions) -> CopyStats:
        """Copy using C++ engine"""
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
            print(f"C++ engine failed, falling back to Python: {e}")
            return self._copy_with_py_engine(source_paths, destination_paths, options)
    
    def _copy_with_py_engine(self, source_paths: List[str], destination_paths: List[str], 
                            options: CopyOptions) -> CopyStats:
        """Copy using Python engine"""
        try:
            # Convert to Python options
            py_options = PyCopyOptions(
                block_size=options.block_size,
                thread_count=options.thread_count,
                use_direct_io=bool(options.use_direct_io),  # Convert to bool
                verify_integrity=options.verify_integrity,
                hash_algorithm=options.hash_algorithm,
                mtu_size=options.mtu_size,
                socket_buffer_size=options.socket_buffer_size,
                adaptive_parameters=options.adaptive_parameters,
                large_file_threshold=options.large_file_threshold
            )
            
            # Perform copy
            py_stats = self.py_engine.copy_files(source_paths, destination_paths, py_options)
            
            # Convert to our stats format
            stats = CopyStats(
                total_files=py_stats.total_files,
                copied_files=py_stats.copied_files,
                total_bytes=py_stats.total_bytes,
                copied_bytes=py_stats.copied_bytes,
                start_time=py_stats.start_time,
                end_time=py_stats.end_time,
                speed_mbps=py_stats.speed_mbps,
                errors=py_stats.errors,
                hash_verifications=py_stats.hash_verifications,
                hash_failures=py_stats.hash_failures
            )
            
            return stats
            
        except Exception as e:
            print(f"Python engine also failed: {e}")
            # Return empty stats with error
            stats = CopyStats()
            stats.errors.append(f"Both engines failed: {e}")
            return stats
    
    def test_bandwidth(self) -> Dict[str, float]:
        """Test disk bandwidth using the best available method"""
        if self.cpp_engine:
            try:
                bandwidth_test = cpp_engine.test_disk_bandwidth("")  # Pass empty string as argument
                return {
                    "write_speed": bandwidth_test.write_speed,
                    "read_speed": bandwidth_test.read_speed,
                    "avg_speed": bandwidth_test.avg_speed
                }
            except Exception as e:
                print(f"C++ bandwidth test failed: {e}")
        
        # Fallback to Python
        if self.py_engine:
            try:
                from app.utils.enhanced_file_copy import BandwidthDetector
                bandwidth_test = BandwidthDetector.test_disk_bandwidth()
                return {
                    "write_speed": bandwidth_test["write_speed"],
                    "read_speed": bandwidth_test["read_speed"],
                    "avg_speed": bandwidth_test["avg_speed"]
                }
            except Exception as e:
                print(f"Python bandwidth test failed: {e}")
        
        # Default fallback
        return {"write_speed": 100.0, "read_speed": 100.0, "avg_speed": 100.0}
    
    def get_optimal_parameters(self, bandwidth_mbps: float = 0.0) -> Dict[str, Any]:
        """Get optimal parameters based on bandwidth"""
        if self.cpp_engine:
            try:
                return cpp_engine.get_optimal_parameters(bandwidth_mbps)
            except Exception as e:
                print(f"C++ optimal parameters failed: {e}")
        
        # Fallback to Python
        if self.py_engine:
            try:
                from app.utils.enhanced_file_copy import BandwidthDetector
                return BandwidthDetector.get_optimal_parameters(bandwidth_mbps)
            except Exception as e:
                print(f"Python optimal parameters failed: {e}")
        
        # Default fallback with safer defaults
        return {
            "block_size": 4 * 1024 * 1024,  # 4MB default
            "thread_count": 2,  # Conservative default
            "use_direct_io": False,  # Buffered by default
            "large_file_threshold": 256 * 1024 * 1024  # 256MB
        }
    
    def calculate_file_hash(self, file_path: str, algorithm: str = "xxhash64") -> str:
        """Calculate file hash using the best available method"""
        if self.cpp_engine:
            try:
                return cpp_engine.calculate_file_hash(file_path, algorithm)
            except Exception as e:
                print(f"C++ hash calculation failed: {e}")
        
        # Fallback to Python
        if self.py_engine:
            try:
                from app.utils.enhanced_file_copy import HashCalculator
                return HashCalculator.calculate_file_hash(file_path, algorithm)
            except Exception as e:
                print(f"Python hash calculation failed: {e}")
        
        return ""

# Convenience functions
def copy_files(source_paths: List[str], destination_paths: List[str], **kwargs) -> CopyStats:
    """Copy files using the best available engine with auto-tuning"""
    engine = CppEnhancedCopyEngine()
    
    # Filter out unsupported parameters for Python fallback
    supported_kwargs = {k: v for k, v in kwargs.items() 
                       if k in ['block_size', 'thread_count', 'use_direct_io', 
                               'verify_integrity', 'hash_algorithm', 'progress_callback',
                               'adaptive_parameters', 'large_file_threshold', 'files_in_flight', 'ranges_per_file']}
    
    options = CopyOptions(**supported_kwargs)
    return engine.copy_files(source_paths, destination_paths, options)

def copy_file(source_path: str, destination_path: str, **kwargs) -> CopyStats:
    """Copy a single file using the best available engine with auto-tuning"""
    # For single file copy, the destination should be a file path, not a directory
    # The C++ engine expects destination_paths to be directories, so we need to extract the directory
    if os.path.isfile(source_path):
        # Single file copy - destination should be the directory containing the file
        dest_dir = os.path.dirname(destination_path)
        # The C++ engine will copy the file to the destination directory with the same name
        return copy_files([source_path], [dest_dir], **kwargs)
    else:
        # Directory copy
        return copy_files([source_path], [destination_path], **kwargs)

def copy_directory(source_dir: str, destination_dir: str, **kwargs) -> CopyStats:
    """Copy a directory using the best available engine with auto-tuning"""
    return copy_files([source_dir], [destination_dir], **kwargs)

def test_bandwidth() -> Dict[str, float]:
    """Test disk bandwidth"""
    engine = CppEnhancedCopyEngine()
    return engine.test_bandwidth()

def get_optimal_parameters(bandwidth_mbps: float = 0.0) -> Dict[str, Any]:
    """Get optimal parameters based on bandwidth"""
    engine = CppEnhancedCopyEngine()
    return engine.get_optimal_parameters(bandwidth_mbps)

def calculate_file_hash(file_path: str, algorithm: str = "xxhash64") -> str:
    """Calculate file hash"""
    engine = CppEnhancedCopyEngine()
    return engine.calculate_file_hash(file_path, algorithm)

# Export the main engine class
__all__ = [
    'CppEnhancedCopyEngine', 'CopyStats', 'CopyOptions', 'PathAnalyzer',
    'copy_files', 'copy_file', 'copy_directory',
    'test_bandwidth', 'get_optimal_parameters', 'calculate_file_hash',
    'CPP_ENGINE_AVAILABLE'
]
