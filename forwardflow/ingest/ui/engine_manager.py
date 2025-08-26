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
                from ..engines.High_perf.enhanced_high_perf_engine import EnhancedHighPerfTransferEngine
                if sink:
                    _engine_instance = EnhancedHighPerfTransferEngine(sink=sink)
                else:
                    _engine_instance = EnhancedHighPerfTransferEngine()
                print("DEBUG: C++ engine created successfully")
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
