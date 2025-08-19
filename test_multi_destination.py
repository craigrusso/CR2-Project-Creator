#!/usr/bin/env python3
"""
Test script for multi-destination fan-out functionality.
Tests both C++ engine (if available) and Python fallback.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_multi_destination():
    """Test multi-destination fan-out functionality"""
    print("Testing multi-destination fan-out functionality...")
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source directory with test files
        source_dir = temp_path / "source"
        source_dir.mkdir()
        
        # Create destination directories
        dest1_dir = temp_path / "dest1"
        dest2_dir = temp_path / "dest2"
        dest1_dir.mkdir()
        dest2_dir.mkdir()
        
        # Create test files
        test_files = [
            ("test1.txt", b"This is test file 1 with some content"),
            ("test2.txt", b"This is test file 2 with different content"),
            ("large_test.bin", b"0" * 1024 * 1024),  # 1MB file
        ]
        
        for filename, content in test_files:
            file_path = source_dir / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        print(f"Source: {source_dir}")
        print(f"Destinations: {dest1_dir}, {dest2_dir}")
        
        # Test 1: Try C++ engine first
        print("\n=== Testing C++ Engine ===")
        try:
            # Import C++ engine
            from forwardflow.ingest.engines import enhanced_high_perf_engine as cpp_engine
            
            # Create a proper event sink
            class TestEventSink:
                def __init__(self):
                    self.events = []
                
                def emit(self, event_type, payload):
                    self.events.append((event_type, payload))
                    print(f"Event: {event_type} - {payload}")
            
            event_sink = TestEventSink()
            
            # Test the C++ engine directly
            from forwardflow.ingest.engines.enhanced_high_perf_engine import (
                CopyJob, TunedParams, pick_params_for_destination
            )
            
            # Test parameter picking
            params1 = pick_params_for_destination(str(dest1_dir))
            params2 = pick_params_for_destination(str(dest2_dir))
            print(f"Destination 1 params: {params1}")
            print(f"Destination 2 params: {params2}")
            
            # Test file copy
            source_file = source_dir / "test1.txt"
            dest_paths = [str(dest1_dir / "test1.txt"), str(dest2_dir / "test1.txt")]
            
            # Create copy job
            job = CopyJob()
            job.source_paths = [str(source_file)]
            job.destination_paths = dest_paths
            job.block_size = 1024 * 1024  # 1MB
            job.verify_mode = "FAST"
            
            # Test the copy
            engine = cpp_engine.EnhancedHighPerfTransferEngine()
            success = engine.copy_files(job, event_sink.emit)
            
            if success:
                print("✓ C++ engine test successful")
                # Verify files exist
                for dest_path in dest_paths:
                    if Path(dest_path).exists():
                        print(f"✓ File copied to {dest_path}")
                    else:
                        print(f"✗ File missing at {dest_path}")
            else:
                print("✗ C++ engine test failed")
                
        except ImportError as e:
            print(f"✗ C++ engine not available: {e}")
        except Exception as e:
            print(f"✗ C++ engine test failed: {e}")
        
        # Test 2: Python engine fallback
        print("\n=== Testing Python Engine ===")
        try:
            from forwardflow.ingest.engines.python_engine import PythonCopyEngine
            from forwardflow.ingest.api.models import JobSpec, JobOptions
            
            # Create a proper event sink
            class TestEventSink:
                def __init__(self):
                    self.events = []
                
                def emit(self, event_type, payload):
                    self.events.append((event_type, payload))
                    print(f"Event: {event_type} - {payload}")
            
            event_sink = TestEventSink()
            
            # Create job spec with multiple destinations
            job = JobSpec(
                job_id="test_multi_dest",
                source_root=source_dir,
                destination_roots=[dest1_dir, dest2_dir],
                options=JobOptions(
                    mode="FAST",
                    verify_mode="FAST",
                    preset="Auto"
                )
            )
            
            print("✓ Created JobSpec with 2 destinations")
            
            # Create and start engine
            engine = PythonCopyEngine(sink=event_sink)
            print("✓ Python engine created")
            
            print("Starting copy...")
            engine.start(job)
            
            # Verify files exist
            for dest_dir in [dest1_dir, dest2_dir]:
                for filename, _ in test_files:
                    dest_file = dest_dir / filename
                    if dest_file.exists():
                        print(f"✓ File copied to {dest_file}")
                    else:
                        print(f"✗ File missing at {dest_file}")
            
            print("✓ Python engine test completed")
            
        except Exception as e:
            print(f"✗ Python engine test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_multi_destination()
