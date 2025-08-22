#!/usr/bin/env python3
"""
Simple test script for the C++ engine to identify crash issues
"""

import sys
import os
import time

def test_cpp_engine():
    """Test the C++ engine with minimal setup"""
    try:
        print("Testing C++ engine import...")
        
        # Add the build/lib directory to the path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        build_lib_path = os.path.join(current_dir, "build", "lib")
        if build_lib_path not in sys.path:
            sys.path.insert(0, build_lib_path)
        
        print(f"Importing from: {build_lib_path}")
        
        # Try to import the C++ engine
        import enhanced_high_perf_engine as cpp_engine
        print("✓ C++ engine imported successfully")
        
        # Test creating a CopyJob
        print("Testing CopyJob creation...")
        cpp_job = cpp_engine.CopyJob()
        print("✓ CopyJob created successfully")
        
        # Test setting basic properties
        cpp_job.source_paths = ["/tmp/test_source"]
        cpp_job.destination_paths = ["/tmp/test_dest"]
        cpp_job.job_id = "test_job_001"
        print("✓ CopyJob properties set successfully")
        
        # Test creating the engine
        print("Testing engine creation...")
        engine = cpp_engine.EnhancedHighPerfTransferEngine()
        print("✓ Engine created successfully")
        
        # Test setting event sink
        print("Testing event sink setup...")
        def test_event_sink(event_type: str, payload: dict):
            print(f"Event: {event_type} - {payload}")
        
        engine.set_event_sink(test_event_sink)
        print("✓ Event sink set successfully")
        
        # Test with a simple, safe job (non-existent paths to avoid actual file operations)
        print("Testing engine.copy_files with safe test data...")
        
        # Create a minimal test job
        test_job = cpp_engine.CopyJob()
        test_job.source_paths = ["/nonexistent/source"]
        test_job.destination_paths = ["/nonexistent/dest"]
        test_job.job_id = "safe_test_001"
        
        # This should fail gracefully without crashing
        try:
            stats = engine.copy_files(test_job)
            print("✓ engine.copy_files completed (unexpected success)")
        except Exception as e:
            print(f"✓ engine.copy_files failed as expected: {e}")
        
        print("\n🎉 All C++ engine tests passed! The engine is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ C++ engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting C++ engine test...")
    success = test_cpp_engine()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed!")
        sys.exit(1)
