#!/usr/bin/env python3

import sys
import os
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cpp_progress():
    """Test that the C++ engine emits job.progress events correctly"""
    
    print("Testing C++ engine job.progress events...")
    
    try:
        # Import the C++ engine
        from forwardflow.ingest.engines.build.lib import enhanced_high_perf_engine as cpp_engine
        print("✓ C++ engine imported successfully")
        
        # Create a simple test directory structure
        test_dir = Path("/tmp/test_cpp_progress")
        test_dir.mkdir(exist_ok=True)
        
        # Create much larger test files to ensure copy takes longer than 100ms
        for i in range(5):
            test_file = test_dir / f"test_file_{i}.bin"
            with open(test_file, 'wb') as f:
                f.write(b'x' * 50 * 1024 * 1024)  # 50MB each
        
        print(f"✓ Created test files in {test_dir}")
        
        # Track events
        events_received = []
        
        def event_sink(event_type, payload):
            print(f"EVENT: {event_type} - {payload}")
            events_received.append((event_type, payload))
        
        # Create a copy job
        job = cpp_engine.CopyJob()
        job.source_paths = [str(test_dir)]
        job.destination_paths = [str(test_dir / "dest")]
        job.files_in_flight = 1
        job.block_size = 1024 * 1024  # 1MB blocks
        job.large_file_threshold = 10 * 1024 * 1024  # 10MB
        job.ranges_per_file = 1
        job.adaptive_parameters = False
        job.verify_integrity = False
        job.hash_algorithm = "xxhash64"
        job.per_dest_params = []  # Empty list instead of dict
        
        print("✓ Created copy job")
        
        # Create the engine
        engine = cpp_engine.EnhancedHighPerfTransferEngine()
        engine.set_event_sink(event_sink)
        
        print("✓ Created engine with event sink")
        
        # Run the copy
        print("Starting copy...")
        start_time = time.time()
        stats = engine.copy_files(job)
        end_time = time.time()
        
        print(f"✓ Copy completed in {end_time - start_time:.2f}s")
        print(f"Stats: {stats}")
        
        # Check for job.progress events
        job_progress_events = [e for e in events_received if e[0] == "job.progress"]
        print(f"✓ Received {len(job_progress_events)} job.progress events")
        
        if job_progress_events:
            print("Sample job.progress event:")
            print(f"  {job_progress_events[0]}")
        
        # Check for job.started and job.completed events
        job_started = [e for e in events_received if e[0] == "job.started"]
        job_completed = [e for e in events_received if e[0] == "job.completed"]
        
        print(f"✓ job.started events: {len(job_started)}")
        print(f"✓ job.completed events: {len(job_completed)}")
        
        if job_started:
            print(f"  job.started payload: {job_started[0][1]}")
        if job_completed:
            print(f"  job.completed payload: {job_completed[0][1]}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        print("✓ Cleaned up test directory")
        
        return len(job_progress_events) > 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cpp_progress()
    if success:
        print("\n✓ C++ engine job.progress events are working correctly!")
    else:
        print("\n✗ C++ engine job.progress events are not working correctly!")
    sys.exit(0 if success else 1)
