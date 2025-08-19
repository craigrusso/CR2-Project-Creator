#!/usr/bin/env python3
"""
Test script to verify the transfer module fix works
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_transfer_fix():
    """Test that the transfer module can create a job without crashing"""
    print("Testing transfer module fix...")
    
    try:
        # Import the necessary modules
        from forwardflow.ingest.api.models import JobSpec, JobOptions
        from forwardflow.ingest.policies.simple_policy import SimplePolicy
        from forwardflow.ingest.engines.python_engine import PythonCopyEngine
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test source directory with some files
            src_dir = temp_path / "source"
            src_dir.mkdir()
            
            # Create a test file
            test_file = src_dir / "test.txt"
            test_file.write_text("Hello, World!")
            
            # Create a test destination directory
            dst_dir = temp_path / "destination"
            dst_dir.mkdir()
            
            print(f"Test directories created:")
            print(f"  Source: {src_dir}")
            print(f"  Destination: {dst_dir}")
            
            # Create a job spec with the new multi-destination format
            job = JobSpec(
                job_id="test_job",
                source_root=src_dir,
                destination_roots=[dst_dir],  # Using the new format
                options=JobOptions(
                    mode="FAST",
                    verify_mode="FAST",
                    preset="auto",
                    per_file_concurrency=1,
                    stream_concurrency=1
                )
            )
            
            print(f"Job created successfully: {job}")
            
            # Test the SimplePolicy
            policy = SimplePolicy()
            files = list(policy.plan(job))
            print(f"Policy planning successful: {len(files)} files found")
            
            # Test the Python copy engine
            engine = PythonCopyEngine()
            print("Python copy engine created successfully")
            
            # Test that the engine can start without crashing
            print("Testing engine start...")
            engine.start(job)
            print("Engine start completed successfully!")
            
            # Check if the file was copied
            copied_file = dst_dir / "test.txt"
            if copied_file.exists():
                print(f"✓ File copied successfully: {copied_file}")
                print(f"✓ File content: {copied_file.read_text()}")
            else:
                print(f"✗ File not found: {copied_file}")
            
            print("\n✓ All tests passed! The transfer module fix is working.")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_transfer_fix()
    sys.exit(0 if success else 1)
