"""Engine Manager for handling Rust engine imports"""

import threading
from typing import Optional

# Global engine instance
_engine_instance = None
_engine_lock = threading.Lock()


def get_engine(sink=None):
    """Get the Rust engine instance (singleton pattern) - RUST ENGINE ONLY, NO FALLBACK"""
    global _engine_instance
    
    with _engine_lock:
        if _engine_instance is None:
            try:
                # Use REAL Rust engine from system-wide module - NO FALLBACK
                print("DEBUG: Using REAL Rust engine from system-wide module - NO FALLBACK")
                
                # Import the real Rust engine directly from system-wide module
                import rust_high_perf_engine
                print("DEBUG: Successfully imported real Rust engine from system")
                
                # Create REAL Rust engine instance directly
                _engine_instance = rust_high_perf_engine.PyEnhancedHighPerfTransferEngine()
                print("DEBUG: Created REAL PyEnhancedHighPerfTransferEngine instance")

                # REMOVED: set_event_sink - causes GIL deadlock
                # Event pump architecture is used instead (see controls.py)
                # The event pump is initialized when transfer starts, not during engine creation
                print("DEBUG: Real Rust engine created successfully (event pump will be initialized on transfer start)")
                
            except Exception as e:
                print(f"ERROR: Failed to create Rust engine: {e}")
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"Rust engine is REQUIRED and failed to initialize: {e}")
        
        return _engine_instance


def reset_engine():
    """Reset the engine instance (for testing or error recovery)"""
    global _engine_instance
    
    with _engine_lock:
        _engine_instance = None
        print("DEBUG: Engine instance reset")


def get_engine_type():
    """Get the type of engine currently in use"""
    if _engine_instance is None:
        return "None"
    
    engine_class = _engine_instance.__class__.__name__
    if "Rust" in engine_class or hasattr(_engine_instance, 'rust_engine'):
        return "Rust"
    else:
        return "Unknown"
