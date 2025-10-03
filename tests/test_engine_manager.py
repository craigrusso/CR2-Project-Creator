#!/usr/bin/env python3
"""Test script to verify engine manager works correctly"""

import sys
import os

print("Testing engine manager...")

try:
    # Add the forwardflow path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    forwardflow_path = os.path.join(current_dir, "forwardflow")
    if forwardflow_path not in sys.path:
        sys.path.insert(0, forwardflow_path)
    
    print("Testing engine manager import...")
    from ingest.ui.engine_manager import get_engine, reset_engine
    print("✓ Engine manager imported successfully!")
    
    print("Testing engine creation...")
    engine = get_engine()
    print(f"✓ Engine created: {engine}")
    
    print("Testing engine reset...")
    reset_engine()
    print("✓ Engine reset successfully!")
    
    print("Testing engine recreation...")
    engine2 = get_engine()
    print(f"✓ Engine recreated: {engine2}")
    
    print("Testing CopyJob creation...")
    import enhanced_high_perf_engine as cpp_engine
    copy_job = cpp_engine.CopyJob()
    copy_job.source_paths = ["/tmp/test_source"]
    copy_job.destination_paths = ["/tmp/test_dest"]
    copy_job.job_id = "test_job"
    print(f"✓ CopyJob created: {copy_job}")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
