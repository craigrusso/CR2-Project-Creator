"""
Rust High Performance Engine Module
This module loads the real Rust engine - NO FALLBACK ENGINE
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Try to load the real Rust engine via the loader
try:
    # Import the Rust engine loader
    from .rust_engine_loader import get_engine
    
    print("DEBUG: Successfully imported real Rust engine via loader")
    
except ImportError as e:
    print(f"ERROR: Failed to import real Rust engine: {e}")
    print("ERROR: Rust engine is REQUIRED - NO FALLBACK ENGINE")
    raise RuntimeError(f"Rust engine is REQUIRED and failed to load: {e}")

# Export the engine getter function
__all__ = ['get_engine']