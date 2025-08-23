#!/usr/bin/env python3
"""
Minimal test to isolate C++ engine crash
"""
import sys
import os

def test_cpp_engine():
    print("Testing C++ engine import...")
    
    try:
        # Add the build/lib path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        build_lib_path = os.path.join(current_dir, "forwardflow", "ingest", "engines", "build", "lib")
        print(f"Build lib path: {build_lib_path}")
        
        if build_lib_path not in sys.path:
            sys.path.insert(0, build_lib_path)
            print(f"Added {build_lib_path} to sys.path")
        
        print("Attempting to import enhanced_high_perf_engine...")
        import enhanced_high_perf_engine
        print("✓ C++ engine imported successfully!")
        
        print("Testing basic functionality...")
        engine = enhanced_high_perf_engine.EnhancedHighPerfTransferEngine()
        print("✓ Engine created successfully!")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cpp_engine()
    if success:
        print("C++ engine test PASSED")
    else:
        print("C++ engine test FAILED")
        sys.exit(1)
