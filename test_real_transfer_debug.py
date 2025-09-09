#!/usr/bin/env python3
"""
Test Real Transfer with Debug - triggers actual engine transfer to see debug output
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from forwardflow.ingest.engines.rust_high_perf.rust_high_perf_engine import PyEnhancedHighPerfTransferEngine
    from forwardflow.ingest.ui.rust_event_sink import RustEventSink
    from forwardflow.ingest.ui.event_bridge import EventBridge
    import rust_high_perf_engine
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def test_real_transfer():
    """Test the real transfer path to see debug output"""
    print("=== TESTING REAL TRANSFER PATH ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create a few test files
        for i in range(3):
            file_path = source_dir / f"test_file_{i+1}.txt"
            with open(file_path, 'wb') as f:
                f.write(b'0' * (1024 * (i + 1)))  # 1KB, 2KB, 3KB
        
        print(f"Created test files in: {source_dir}")
        print(f"Files: {list(source_dir.glob('*'))}")
        
        # Initialize engine and event system like the UI does
        print("\n=== INITIALIZING ENGINE ===")
        engine = PyEnhancedHighPerfTransferEngine()
        
        print("\n=== SETTING UP EVENT SYSTEM ===")
        event_sink = RustEventSink()
        
        # Initialize the job on the event sink
        event_sink.initialize_job(3, [str(dest_dir)])
        
        # Set event sink on engine
        engine.set_event_sink(event_sink)
        print("Event sink set on engine")
        
        # Create CopyJob like the UI does
        print("\n=== CREATING COPY JOB ===")
        copy_job = rust_high_perf_engine.CopyJob()
        copy_job.source_paths = [str(source_dir)]
        copy_job.destination_paths = [str(dest_dir)]
        copy_job.job_id = "test_debug_job"
        copy_job.files_in_flight = 2
        copy_job.ranges_per_file = 1
        copy_job.verify_integrity = True
        copy_job.hash_algorithm = "xxhash64"
        copy_job.generate_verification_report = True
        copy_job.use_direct_io = False
        copy_job.block_size = 1024 * 1024
        
        print(f"CopyJob created: source={copy_job.source_paths}, dest={copy_job.destination_paths}")
        
        # Start the copy operation
        print("\n=== STARTING COPY OPERATION ===")
        try:
            result = engine.copy_files(copy_job)
            print(f"\n=== COPY RESULT ===")
            print(f"Result: {result}")
            
            # Check if files were copied
            dest_files = list(dest_dir.glob('*'))
            print(f"Files in destination: {dest_files}")
            
        except Exception as e:
            print(f"Error during copy: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_real_transfer()