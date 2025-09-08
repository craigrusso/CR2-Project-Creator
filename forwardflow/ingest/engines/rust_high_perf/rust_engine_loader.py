"""
Rust Engine Loader - Loads the real Rust engine library
This is NOT an engine - it's just a loader for the real Rust engine
"""

import os
import sys
import ctypes
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def get_engine():
    """Get the Rust engine with loud fallback to stub"""
    try:
        # First try the custom Python module
        from .rust_high_perf_engine import PyEnhancedHighPerfTransferEngine
        eng = PyEnhancedHighPerfTransferEngine()
        print("[RustEngineLoader] Loaded PyEnhancedHighPerfTransferEngine from custom module")
        return eng
    except Exception as e:
        print(f"[RustEngineLoader] Custom module failed: {e}")
        try:
            # Fallback to wrapper
            from .rust_high_perf_engine_wrapper import RustHighPerfEngineWrapper
            eng = RustHighPerfEngineWrapper()
            print("[RustEngineLoader] Loaded RustHighPerfEngineWrapper")
            return eng
        except Exception as e2:
            print(f"[RustEngineLoader][FALLBACK] Using stub engine due to error: {e2}")
            # Previous stub, but keep it very loud:
            class Stub:
                def set_event_sink(self, *_a, **_k): pass
                def copy_files(self, *_a, **_k):
                    return {"warning": "STUB ENGINE ACTIVE; no real copy performed"}
                def get_enhanced_stats(self):
                    return {"warning": "STUB ENGINE ACTIVE"}
            return Stub()

# Create an alias for the engine manager to import
def PyEnhancedHighPerfTransferEngine():
    """Factory function that returns a RustHighPerfEngineWrapper instance"""
    return get_engine()

# Export the engine getter and the class alias for use by the engine manager
__all__ = ['get_engine', 'PyEnhancedHighPerfTransferEngine']
