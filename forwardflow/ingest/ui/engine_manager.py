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
                # Use Rust engine ONLY - NO FALLBACK
                print("DEBUG: Using Rust engine - NO FALLBACK")
                
                # Import the real Rust engine from the built module
                import sys
                import os
                
                # Add the rust_high_perf directory to the path
                rust_engine_path = os.path.join(os.path.dirname(__file__), '..', 'engines', 'rust_high_perf')
                sys.path.insert(0, rust_engine_path)
                
                # Import the real Rust engine via loader - NO FALLBACK
                from forwardflow.ingest.engines.rust_high_perf.rust_engine_loader import PyEnhancedHighPerfTransferEngine
                print("DEBUG: Successfully imported real Rust engine via loader")
                
                # Create Rust engine instance directly
                _engine_instance = PyEnhancedHighPerfTransferEngine()
                
                # Use the Rust event sink wrapper if no sink provided
                if sink is None:
                    from .rust_event_sink import RustEventSink
                    sink = RustEventSink()
                
                # Set the event sink
                _engine_instance.set_event_sink(sink)
                print("DEBUG: Real Rust engine created successfully with event sink")
                
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
