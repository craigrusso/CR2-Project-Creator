"""Load the compiled rust_high_perf_engine PyO3 extension."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_native_module() -> ModuleType:
    """Resolve and load the compiled extension that ships with this package."""

    current_dir = Path(__file__).parent
    candidates = (
        current_dir / "rust_high_perf_engine.so",
        current_dir / "rust_high_perf_engine.pyd",
        current_dir / "rust_high_perf_engine.dylib",
        current_dir / "librust_high_perf_engine.so",
        current_dir / "librust_high_perf_engine.dylib",
    )

    for candidate in candidates:
        if not candidate.exists():
            continue

        loader = importlib.machinery.ExtensionFileLoader(__name__, str(candidate))
        spec = importlib.util.spec_from_loader(__name__, loader)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.__file__ = str(candidate)
        module.__loader__ = loader
        return module

    raise ImportError(
        "Unable to locate the compiled rust_high_perf_engine extension. "
        "Expected one of: "
        + ", ".join(str(path) for path in candidates)
    )


_native = _load_native_module()

# Replace this shim with the compiled module so downstream imports get the real engine.
sys.modules[__name__] = _native

# Mirror the compiled module namespace for already-imported references.
globals().update(_native.__dict__)

