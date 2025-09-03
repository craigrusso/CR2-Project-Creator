"""Engine Manager for handling C++ engine imports"""

import threading
from typing import Optional

# Global engine instance
_engine_instance = None
_engine_lock = threading.Lock()


def get_engine(sink=None):
    """Get the C++ engine instance (singleton pattern)"""
    global _engine_instance
    
    with _engine_lock:
        if _engine_instance is None:
            try:
                # Try to import from the build/lib directory first
                import sys
                import os
                
                # Add the build/lib path to sys.path if not already there
                current_dir = os.path.dirname(os.path.abspath(__file__))
                build_lib_path = os.path.join(current_dir, "..", "engines", "build", "lib")
                if build_lib_path not in sys.path:
                    sys.path.insert(0, build_lib_path)
                
                import enhanced_high_perf_engine as cpp_engine
                _engine_instance = cpp_engine.EnhancedHighPerfTransferEngine()
                
                # Use the new C++ event sink wrapper if no sink provided
                if sink is None:
                    from .cpp_event_sink import CppEventSink
                    sink = CppEventSink()
                
                _engine_instance.set_event_sink(sink)
                print("DEBUG: C++ engine created successfully with event sink")
            except Exception as e:
                print(f"DEBUG: Failed to create C++ engine: {e}")
                raise
        
        return _engine_instance


def reset_engine():
    """Reset the engine instance (for testing or error recovery)"""
    global _engine_instance
    
    with _engine_lock:
        _engine_instance = None
        print("DEBUG: C++ engine instance reset")
