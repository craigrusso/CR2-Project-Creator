"""
Enhanced High-Performance Copy Engine Package

This package provides a high-performance file copying engine that beats Finder on macOS
and scales up for high-speed networks (1/10/25/40/100 GbE) across macOS, Windows, and Linux.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the path so we can import the wrapper
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent.parent / "app"
if app_dir.exists():
    sys.path.insert(0, str(app_dir.parent))

# Try to import the C++ engine
try:
    import enhanced_high_perf_engine as cpp_engine
    CPP_ENGINE_AVAILABLE = True
except ImportError:
    CPP_ENGINE_AVAILABLE = False

# Import the Python wrapper
try:
    from app.utils.cpp_enhanced_copy import (
        CppEnhancedCopyEngine, CopyOptions, CopyStats, PathAnalyzer,
        copy_file, copy_files, test_bandwidth
    )
    PY_WRAPPER_AVAILABLE = True
except ImportError:
    PY_WRAPPER_AVAILABLE = False

# Create a simple fallback if the main wrapper isn't available
if not PY_WRAPPER_AVAILABLE:
    class CopyStats:
        def __init__(self):
            self.total_files = 0
            self.copied_files = 0
            self.total_bytes = 0
            self.copied_bytes = 0
            self.start_time = 0.0
            self.end_time = 0.0
            self.speed_mbps = 0.0
            self.errors = []
            self.hash_verifications = 0
            self.hash_failures = 0
        
        def duration(self):
            return self.end_time - self.start_time
        
        def success_rate(self):
            return (self.copied_files * 100.0) / self.total_files if self.total_files > 0 else 0.0

    class CopyOptions:
        def __init__(self, **kwargs):
            self.block_size = kwargs.get('block_size', 4 * 1024 * 1024)
            self.thread_count = kwargs.get('thread_count', 0)
            self.use_direct_io = kwargs.get('use_direct_io', False)
            self.verify_integrity = kwargs.get('verify_integrity', False)
            self.hash_algorithm = kwargs.get('hash_algorithm', 'xxhash64')
            self.mtu_size = kwargs.get('mtu_size', 0)
            self.socket_buffer_size = kwargs.get('socket_buffer_size', 0)
            self.adaptive_parameters = kwargs.get('adaptive_parameters', True)
            self.large_file_threshold = kwargs.get('large_file_threshold', 256 * 1024 * 1024)
            self.progress_callback = kwargs.get('progress_callback', None)

    class CppEnhancedCopyEngine:
        def __init__(self):
            self.cpp_engine = None
            self.py_engine = None
        
        def copy_files(self, source_paths, destination_paths, options=None):
            # Fallback to basic file operations
            stats = CopyStats()
            stats.errors.append("Enhanced copy engine not available, using fallback")
            return stats

    def copy_file(source_path, destination_path, **kwargs):
        stats = CopyStats()
        stats.errors.append("Enhanced copy engine not available")
        return stats

    def copy_files(source_paths, destination_paths, **kwargs):
        stats = CopyStats()
        stats.errors.append("Enhanced copy engine not available")
        return stats

    def test_bandwidth():
        return {"write_speed": 100.0, "read_speed": 100.0, "avg_speed": 100.0}

    class PathAnalyzer:
        @staticmethod
        def is_usb_or_thunderbolt(path):
            return False
        
        @staticmethod
        def is_network_path(path):
            return False
        
        @staticmethod
        def is_nvme_path(path):
            return False

# Export the main components
__all__ = [
    'CppEnhancedCopyEngine',
    'CopyOptions', 
    'CopyStats',
    'PathAnalyzer',
    'copy_file',
    'copy_files',
    'test_bandwidth',
    'CPP_ENGINE_AVAILABLE',
    'PY_WRAPPER_AVAILABLE'
]

# Version info
__version__ = "1.0.0"
__author__ = "ForwardFlow Team"

def get_engine_info():
    """Get information about the available engines"""
    return {
        "cpp_engine_available": CPP_ENGINE_AVAILABLE,
        "python_wrapper_available": PY_WRAPPER_AVAILABLE,
        "version": __version__,
        "platform": sys.platform,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }

def is_enhanced_copy_available():
    """Check if the enhanced copy engine is available"""
    return CPP_ENGINE_AVAILABLE and PY_WRAPPER_AVAILABLE
