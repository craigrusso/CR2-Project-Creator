#!/usr/bin/env python3
"""Test script to see exactly what error occurs when importing the C++ engine"""

import sys
import os

print("Testing C++ engine import...")

try:
    # Add the build/lib path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    build_lib_path = os.path.join(current_dir, "forwardflow", "ingest", "engines", "build", "lib")
    print(f"Build lib path: {build_lib_path}")
    
    if build_lib_path not in sys.path:
        sys.path.insert(0, build_lib_path)
        print(f"Added {build_lib_path} to sys.path")
    
    print("Attempting to import C++ engine...")
    import enhanced_high_perf_engine as cpp_engine
    print("✓ C++ engine imported successfully!")
    
    print("Available attributes:", [attr for attr in dir(cpp_engine) if not attr.startswith('_')])
    
except Exception as e:
    print(f"✗ Error importing C++ engine: {e}")
    import traceback
    traceback.print_exc()
