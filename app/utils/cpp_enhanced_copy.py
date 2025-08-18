#!/usr/bin/env python3
"""
C++ Enhanced Copy Engine Wrapper

This module provides a Python interface to the C++ enhanced high-performance
file copying engine for maximum performance.
"""

import os
import sys
import time
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path

# Try to import the C++ engine
try:
    from forwardflow.ingest.engines.build.lib import enhanced_high_perf_engine as cpp_engine
    CPP_ENGINE_AVAILABLE = True
except ImportError:
    CPP_ENGINE_AVAILABLE = False
    print("Warning: C++ enhanced copy engine not available, falling back to Python implementation")

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
    """Options for copy operations"""
    block_size: int = 1024 * 1024  # 1MB default
    thread_count: int = 0  # 0 = auto-detect
    use_direct_io: bool = True
    verify_integrity: bool = True
    hash_algorithm: str = "xxhash64"
    mtu_size: int = 0  # 0 = auto-detect
    socket_buffer_size: int = 0  # 0 = auto-detect
    adaptive_parameters: bool = True
    large_file_threshold: int = 100 * 1024 * 1024  # 100MB
    progress_callback: Optional[Callable] = None

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
    
    def copy_files(self, source_paths: List[str], destination_paths: List[str], 
                   options: Optional[CopyOptions] = None) -> CopyStats:
        """
        Copy files using the best available engine
        
        Args:
            source_paths: List of source file/directory paths
            destination_paths: List of destination paths
            options: Copy options
            
        Returns:
            CopyStats: Statistics from the copy operation
        """
        if options is None:
            options = CopyOptions()
        
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
            cpp_job.block_size = options.block_size
            cpp_job.thread_count = options.thread_count
            cpp_job.use_direct_io = options.use_direct_io
            cpp_job.verify_integrity = options.verify_integrity
            cpp_job.hash_algorithm = options.hash_algorithm
            cpp_job.mtu_size = options.mtu_size
            cpp_job.socket_buffer_size = options.socket_buffer_size
            cpp_job.adaptive_parameters = options.adaptive_parameters
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
                use_direct_io=options.use_direct_io,
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
        
        # Default fallback
        return {
            "block_size": 1024 * 1024,
            "thread_count": 4,
            "use_direct_io": True,
            "large_file_threshold": 100 * 1024 * 1024
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
    """Copy files using the best available engine"""
    engine = CppEnhancedCopyEngine()
    options = CopyOptions(**kwargs)
    return engine.copy_files(source_paths, destination_paths, options)

def copy_file(source_path: str, destination_path: str, **kwargs) -> CopyStats:
    """Copy a single file using the best available engine"""
    return copy_files([source_path], [destination_path], **kwargs)

def copy_directory(source_dir: str, destination_dir: str, **kwargs) -> CopyStats:
    """Copy a directory using the best available engine"""
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
    'CppEnhancedCopyEngine', 'CopyStats', 'CopyOptions',
    'copy_files', 'copy_file', 'copy_directory',
    'test_bandwidth', 'get_optimal_parameters', 'calculate_file_hash',
    'CPP_ENGINE_AVAILABLE'
]
