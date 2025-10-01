"""High-level loader for the compiled Rust transfer engine."""

from .rust_high_perf_engine_wrapper import RustHighPerfEngineWrapper


def get_engine() -> RustHighPerfEngineWrapper:
    """Instantiate the production Rust engine wrapper."""

    return RustHighPerfEngineWrapper()


def PyEnhancedHighPerfTransferEngine() -> RustHighPerfEngineWrapper:
    """Compatibility alias for legacy import sites."""

    return get_engine()


__all__ = ["get_engine", "PyEnhancedHighPerfTransferEngine"]
