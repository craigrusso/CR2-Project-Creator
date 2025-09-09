"""
Test implementation for multi-destination copy with live progress updates.

This script demonstrates the DIT-grade multi-destination copy functionality
with continuous progress emission and proper event handling.
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def create_test_files(base_path: Path, num_files: int = 10, file_size_mb: int = 1) -> None:
    """Create test files for copying"""
    base_path.mkdir(parents=True, exist_ok=True)
    
    for i in range(num_files):
        test_file = base_path / f"test_file_{i:03d}.bin"
        with open(test_file, 'wb') as f:
            # Write random data
            f.write(os.urandom(file_size_mb * 1024 * 1024))
        print(f"Created test file: {test_file}")

def test_multi_destination_copy():
    """Test multi-destination copy with live progress updates"""
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source directory with test files
        source_dir = temp_path / "source"
        create_test_files(source_dir, num_files=5, file_size_mb=2)
        
        # Create destination directories
        dest1 = temp_path / "dest1"
        dest2 = temp_path / "dest2"
        dest3 = temp_path / "dest3"
        
        dest1.mkdir()
        dest2.mkdir()
        dest3.mkdir()
        
        print(f"Source directory: {source_dir}")
        print(f"Destination directories: {dest1}, {dest2}, {dest3}")
        
        # Event tracking
        events_received = []
        
        def event_sink(event_type: str, payload: Dict[str, Any]) -> None:
            """Event sink for tracking progress"""
            events_received.append((event_type, payload))
            print(f"[EVT] {event_type}: {payload}")
        
        try:
            # Import and initialize the engine
            from forwardflow.ingest.engines.rust_high_perf import get_engine
            engine = get_engine()
            
            # Set up event handling
            engine.set_event_sink(event_sink)
            
            # Create CopyJob
            from rust_high_perf_engine import CopyJob
            job = CopyJob()
            job.source_paths = [str(source_dir)]
            job.destination_paths = [str(dest1), str(dest2), str(dest3)]
            job.job_id = "test_multi_dest_001"
            job.files_in_flight = 2
            job.ranges_per_file = 1
            job.verify_integrity = True
            job.hash_algorithm = "xxh64"
            job.generate_verification_report = True
            job.use_direct_io = False
            job.block_size = 4 * 1024 * 1024  # 4MB
            
            print(f"Starting multi-destination copy job: {job.job_id}")
            print(f"Source: {job.source_paths}")
            print(f"Destinations: {job.destination_paths}")
            
            # Start the copy operation
            start_time = time.time()
            result = engine.copy_files(job)
            end_time = time.time()
            
            print(f"\nCopy operation completed in {end_time - start_time:.2f} seconds")
            print(f"Result: {result}")
            
            # Analyze events received
            print(f"\nEvents received: {len(events_received)}")
            event_types = {}
            for event_type, payload in events_received:
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            print("Event summary:")
            for event_type, count in event_types.items():
                print(f"  {event_type}: {count}")
            
            # Verify files were copied to all destinations
            for dest in [dest1, dest2, dest3]:
                dest_files = list(dest.glob("*.bin"))
                print(f"Files in {dest}: {len(dest_files)}")
                for file_path in dest_files:
                    print(f"  {file_path.name}: {file_path.stat().st_size} bytes")
            
            # Test enhanced stats
            stats = engine.get_enhanced_stats()
            print(f"\nEnhanced stats: {stats}")
            
        except Exception as e:
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

def test_console_event_sink():
    """Test with console event sink for debugging"""
    
    def console_sink(event_type: str, payload: Dict[str, Any]) -> None:
        """Simple console event sink"""
        print(f"[EVT] {event_type}: {payload}")
    
    try:
        from forwardflow.ingest.engines.rust_high_perf import get_engine
        engine = get_engine()
        
        # Set up console event sink
        engine.set_event_sink(console_sink)
        
        print("Engine loaded successfully with console event sink")
        print("Ready for multi-destination copy testing")
        
        return True
        
    except Exception as e:
        print(f"Failed to load engine: {e}")
        return False

if __name__ == "__main__":
    print("=== DIT-Grade Multi-Destination Copy Test ===")
    print()
    
    # Test 1: Console event sink
    print("Test 1: Console event sink")
    if test_console_event_sink():
        print("✓ Console event sink test passed")
    else:
        print("✗ Console event sink test failed")
    
    print()
    
    # Test 2: Full multi-destination copy
    print("Test 2: Multi-destination copy with live progress")
    if test_multi_destination_copy():
        print("✓ Multi-destination copy test passed")
    else:
        print("✗ Multi-destination copy test failed")
    
    print("\n=== Test Complete ===")
