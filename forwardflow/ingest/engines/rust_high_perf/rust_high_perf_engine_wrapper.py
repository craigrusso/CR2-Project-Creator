"""
Python wrapper for the Rust high-performance engine.

This wrapper provides a clean interface to the Rust engine while handling
Python-specific conversions and error handling.
"""

import os
import sys
import threading
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path

try:
    from PyQt6 import QtCore
    HAS_QT = True
    print("DEBUG: Using PyQt6 for Rust engine wrapper")
except Exception as e:
    print(f"DEBUG: PyQt6 not available: {e}")
    HAS_QT = False

# Import the Rust engine module - use the COMPILED library installed system-wide
# We need to avoid importing the local stub module that shadows the compiled library
import sys
import importlib

# Temporarily remove this directory from sys.path to avoid importing the local stub
current_dir = os.path.dirname(__file__)
if current_dir in sys.path:
    sys.path.remove(current_dir)

try:
    # Force import from system-wide installation, not local stub
    if 'rust_high_perf_engine' in sys.modules:
        del sys.modules['rust_high_perf_engine']  # Clear any cached import
    
    # Import the REAL compiled Rust library from system packages
    import rust_high_perf_engine
    print(f"DEBUG: Successfully imported compiled Rust engine from: {getattr(rust_high_perf_engine, '__file__', 'unknown')}")
    
    # Import the actual PyO3 classes from the compiled library
    PyEnhancedHighPerfTransferEngine = rust_high_perf_engine.PyEnhancedHighPerfTransferEngine
    CopyJob = rust_high_perf_engine.CopyJob  
    CopyStats = rust_high_perf_engine.CopyStats
    
    print("DEBUG: Successfully imported all classes from compiled Rust engine")
    print(f"DEBUG: PyEnhancedHighPerfTransferEngine: {PyEnhancedHighPerfTransferEngine}")
    print(f"DEBUG: CopyJob: {CopyJob}")
    print(f"DEBUG: CopyStats: {CopyStats}")
    
except ImportError as e:
    print(f"ERROR: Failed to import compiled Rust engine: {e}")
    # Restore the current directory to path for fallback
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Last resort - try the stub module
    try:
        from .rust_high_perf_engine import (
            PyEnhancedHighPerfTransferEngine,
            CopyJob,
            CopyStats
        )
        print("WARNING: Using stub Rust engine - performance will be severely limited!")
    except ImportError as e2:
        print(f"CRITICAL ERROR: No Rust engine available: {e2}")
        raise e

finally:
    # Restore current directory to path if it was removed
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


class _QtEmitter(QtCore.QObject if HAS_QT else object):
    """Qt emitter for marshaling events to the main thread"""
    if HAS_QT:
        # Define signal as class attribute
        signal = QtCore.pyqtSignal(str, dict)  # (event_type, payload)

        def __init__(self, sink: Callable[[str, Dict[str, Any]], None]):
            super().__init__()
            self._sink = sink
            # Connect signal to our handler
            self.signal.connect(self._handle_signal)
        
        def _handle_signal(self, event_type, payload):
            """Handle the signal and call the sink"""
            try:
                self._sink(event_type, payload)
            except Exception as e:
                print(f"DEBUG: Error in signal handler: {e}")
        
        def emit(self, event_type, payload):
            """Emit the signal"""
            try:
                self.signal.emit(event_type, payload)
            except Exception as e:
                print(f"DEBUG: Error emitting signal: {e}")
    else:
        # Fallback: direct call (non-Qt)
        def __init__(self, sink):
            self._sink = sink
        def emit(self, event_type, payload):
            self._sink(event_type, payload)


class RustHighPerfEngineWrapper:
    """
    Python wrapper for the Rust high-performance transfer engine.
    
    This class provides a clean interface to the Rust engine while handling
    Python-specific conversions and maintaining compatibility with the existing
    engine interface.
    """
    
    def __init__(self):
        """Initialize the Rust engine wrapper."""
        try:
            self.rust_engine = PyEnhancedHighPerfTransferEngine()
            self._normalizer = self._default_normalizer()
            self._qt_sink = None
            print("DEBUG: Rust engine wrapper initialized successfully")
        except Exception as e:
            print(f"ERROR: Failed to initialize Rust engine: {e}")
            raise
    
    def _default_normalizer(self):
        """Map Rust -> UI: event name & keys; adjust to your UI schema here."""
        def normalize(event_type: str, payload: Dict[str, Any]):
            # Example maps job_progress -> progress_update, snake_case -> camelCase
            et = {"job_progress": "progress_update"}.get(event_type, event_type)
            pl = dict(payload)

            # Key renames snake_case -> camelCase
            mapping = {
                "bytes_copied": "bytesCopied",
                "total_bytes": "totalBytes",
                "files_completed": "completedFiles",
                "total_files": "totalFiles",
                "elapsed_s": "elapsedS",
                "speed_mib_s": "avgSpeedMiBps",
                "current_speed_mib_s": "currentSpeedMiBps",
                "peak_speed_mib_s": "peakSpeedMiBps",
                "file_id": "fileId",
                "dest_path": "destPath",
            }
            for k_src, k_dst in mapping.items():
                if k_src in pl:
                    pl[k_dst] = pl.pop(k_src)

            return et, pl
        return normalize
    
    def set_event_sink(self, sink: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Set the event sink for receiving engine events.
        This marshals into the Qt main thread if PyQt is present.
        
        Args:
            sink: Event sink object that will receive engine events
        """
        try:
            # Use direct call approach to avoid Qt signal issues
            def rust_handler(event_type: str, payload: dict):
                try:
                    et, pl = self._normalizer(event_type, payload)
                    sink(et, pl)
                except Exception as e:
                    print(f"DEBUG: Error in event handler: {e}")

            self.rust_engine.set_event_sink(rust_handler)
            print("DEBUG: Rust event sink set successfully")
        except Exception as e:
            print(f"DEBUG: Error setting Rust event sink: {e}")
            import traceback
            traceback.print_exc()
    
    def copy_files(self, rust_job) -> Dict[str, Any]:
        """
        Call into Rust engine, but always return a plain dict with normalized names.
        
        Args:
            rust_job: CopyJob object for the Rust engine
            
        Returns:
            Dictionary containing copy results and statistics with normalized names
        """
        try:
            print(f"DEBUG: Rust engine copy_files called with job: {rust_job}")
            
            # Pass the CopyJob object to the Rust engine
            result = self.rust_engine.copy_files(rust_job)  # PyO3 CopyStats
            
            print(f"DEBUG: Rust engine returned: {result}")
            
            # Map PyO3 attrs -> dict the UI layer expects
            return {
                "jobId": getattr(result, "job_id", ""),
                "startTime": getattr(result, "start_time", 0.0),
                "endTime": getattr(result, "end_time", 0.0),
                "totalFiles": getattr(result, "total_files", 0),
                "completedFiles": getattr(result, "copied_files", getattr(result, "completed_files", 0)),
                "totalBytes": getattr(result, "total_bytes", 0),
                "completedBytes": getattr(result, "copied_bytes", getattr(result, "completed_bytes", 0)),
                # Use MiB/s consistently
                "avgSpeedMiBps": getattr(result, "speed_mbps", getattr(result, "speed_mib_s", 0.0)),
                "dataMiBps": getattr(result, "data_mbps", getattr(result, "data_mib_s", 0.0)),
                "dataElapsedS": getattr(result, "data_elapsed_s", 0.0),
                "errors": list(getattr(result, "errors", [])),
                "fileRecords": list(getattr(result, "files", getattr(result, "file_records", []))),
            }
            
        except Exception as e:
            print(f"ERROR: Rust engine copy_files failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': f'Rust engine error: {str(e)}',
                'files_copied': 0,
                'bytes_copied': 0,
                'errors': [str(e)]
            }
    
    def cancel(self) -> None:
        """Cancel the current operation."""
        try:
            self.rust_engine.cancel()
            print("DEBUG: Rust engine cancel called")
        except Exception as e:
            print(f"ERROR: Rust engine cancel failed: {e}")
    
    def pause(self) -> None:
        """Pause the current operation."""
        try:
            self.rust_engine.pause()
            print("DEBUG: Rust engine pause called")
        except Exception as e:
            print(f"ERROR: Rust engine pause failed: {e}")
    
    def resume(self) -> None:
        """Resume the current operation."""
        try:
            self.rust_engine.resume()
            print("DEBUG: Rust engine resume called")
        except Exception as e:
            print(f"ERROR: Rust engine resume failed: {e}")
    
    def is_cancelled(self) -> bool:
        """Check if the operation is cancelled."""
        try:
            return self.rust_engine.is_cancelled()
        except Exception as e:
            print(f"ERROR: Rust engine is_cancelled failed: {e}")
            return False
    
    def is_paused(self) -> bool:
        """Check if the operation is paused."""
        try:
            return self.rust_engine.is_paused()
        except Exception as e:
            print(f"ERROR: Rust engine is_paused failed: {e}")
            return False
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced statistics with normalized names."""
        try:
            stats = self.rust_engine.get_enhanced_stats()
            # Ensure MiB/s names and camelCase:
            mapping = {
                "bytes_copied": "bytesCopied",
                "total_bytes": "totalBytes",
                "files_completed": "completedFiles",
                "total_files": "totalFiles",
                "elapsed_s": "elapsedS",
                "speed_mib_s": "avgSpeedMiBps",
            }
            out = {}
            for k, v in stats.items():
                out[mapping.get(k, k)] = v
            return out
        except Exception as e:
            print(f"ERROR: Rust engine get_enhanced_stats failed: {e}")
            return {
                'total_files': 0,
                'completed_files': 0,
                'total_bytes': 0,
                'completed_bytes': 0,
                'avgSpeedMiBps': 0.0,
                'file_records': []
            }
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information (legacy method)."""
        return self.get_enhanced_stats()
