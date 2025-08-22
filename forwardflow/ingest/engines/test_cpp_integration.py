#!/usr/bin/env python3
"""
Test script that mimics the actual integration pattern used in the application
"""

import sys
import os
import time
import threading
import queue

def test_cpp_integration():
    """Test the C++ engine with the actual integration pattern"""
    try:
        print("Testing C++ engine integration pattern...")
        
        # Add the build/lib directory to the path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        build_lib_path = os.path.join(current_dir, "build", "lib")
        if build_lib_path not in sys.path:
            sys.path.insert(0, build_lib_path)
        
        print(f"Importing from: {build_lib_path}")
        
        # Import the C++ engine
        import enhanced_high_perf_engine as cpp_engine
        print("✓ C++ engine imported successfully")
        
        # Create a job similar to what the application creates
        print("Creating CopyJob with application-like data...")
        cpp_job = cpp_engine.CopyJob()
        cpp_job.source_paths = ["/Users/craigrusso/Library/CloudStorage/OneDrive-Personal/1_PROJECTS/TUTORIALS_V25.4.0/RECORDS"]
        cpp_job.destination_paths = ["/Volumes/CR_DRIVE/TEST_TRANSFER"]
        cpp_job.preset = "Auto (recommended)"
        cpp_job.verify_mode = "READBACK_VERIFY"
        cpp_job.adaptive_parameters = True
        cpp_job.generate_verification_report = True
        cpp_job.job_id = "test_integration_001"
        print("✓ CopyJob created with application-like data")
        
        # Create the engine
        print("Creating engine...")
        engine = cpp_engine.EnhancedHighPerfTransferEngine()
        print("✓ Engine created successfully")
        
        # Set up event sink similar to the application
        print("Setting up event sink...")
        events_received = []
        
        def event_sink(event_type: str, payload: dict):
            print(f"Event received: {event_type} - {payload}")
            events_received.append((event_type, payload))
        
        engine.set_event_sink(event_sink)
        print("✓ Event sink set successfully")
        
        # Test in a separate thread to mimic the application's background thread
        print("Testing in background thread...")
        result_queue = queue.Queue()
        
        def run_copy_in_thread():
            try:
                print("Thread: Starting copy_files...")
                stats = engine.copy_files(cpp_job)
                print(f"Thread: copy_files completed successfully: {stats}")
                result_queue.put(("success", stats))
            except Exception as e:
                print(f"Thread: copy_files failed: {e}")
                import traceback
                traceback.print_exc()
                result_queue.put(("error", str(e)))
        
        # Start the copy in a background thread
        copy_thread = threading.Thread(target=run_copy_in_thread, daemon=True)
        copy_thread.start()
        
        # Wait for completion with timeout
        print("Waiting for copy to complete...")
        try:
            result_type, result_data = result_queue.get(timeout=30)  # 30 second timeout
            if result_type == "success":
                print("✓ Copy completed successfully in background thread")
                print(f"Stats: {result_data}")
            else:
                print(f"❌ Copy failed in background thread: {result_data}")
                return False
        except queue.Empty:
            print("❌ Copy timed out in background thread")
            return False
        
        # Check events received
        print(f"\nEvents received: {len(events_received)}")
        for event_type, payload in events_received:
            print(f"  - {event_type}: {payload}")
        
        print("\n🎉 C++ engine integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ C++ engine integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting C++ engine integration test...")
    success = test_cpp_integration()
    if success:
        print("Integration test completed successfully!")
    else:
        print("Integration test failed!")
        sys.exit(1)
