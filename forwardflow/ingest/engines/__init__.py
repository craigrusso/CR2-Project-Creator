"""Engine implementations for the ingest module."""

# RUST ENGINE ONLY - NO FALLBACK TO C++
# Import the Rust engine wrapper as the primary engine
try:
    from forwardflow.ingest.engines.rust_high_perf.rust_high_perf_engine_wrapper import RustHighPerfEngineWrapper as EnhancedHighPerfTransferEngine
    RUST_ENGINE_AVAILABLE = True
    print("DEBUG: Rust engine wrapper imported successfully as primary engine")
except ImportError as e:
    print(f"ERROR: Rust engine wrapper import failed: {e}")
    RUST_ENGINE_AVAILABLE = False
    EnhancedHighPerfTransferEngine = None
    raise RuntimeError(f"Rust engine is REQUIRED and failed to load: {e}")

# C++ engine is NOT used - Rust engine is the only engine
CPP_ENGINE_AVAILABLE = False
CppEngine = None

__all__ = ['EnhancedHighPerfTransferEngine', 'RUST_ENGINE_AVAILABLE', 'CppEngine', 'CPP_ENGINE_AVAILABLE']
