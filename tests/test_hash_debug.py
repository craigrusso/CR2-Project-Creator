#!/usr/bin/env python3
"""
Complete test of hash calculation flow to debug why reports show 'Hash: pending'
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_files():
    """Create test files in temp directory"""
    temp_dir = tempfile.mkdtemp(prefix="hash_test_")
    
    # Create source directory with test file
    source_dir = Path(temp_dir) / "source"
    source_dir.mkdir()
    
    test_file = source_dir / "test.txt"
    test_file.write_text("Hello World - Hash Test File")
    
    # Create destination directory
    dest_dir = Path(temp_dir) / "dest"
    dest_dir.mkdir()
    
    print(f"Test files created:")
    print(f"  Source: {source_dir}")
    print(f"  Dest: {dest_dir}")
    print(f"  Test file: {test_file} ({test_file.stat().st_size} bytes)")
    
    return str(source_dir), str(dest_dir), str(test_file)

def test_engine_hash_flow():
    """Test the complete hash calculation flow"""
    
    print("="*60)
    print("TESTING COMPLETE HASH CALCULATION FLOW")
    print("="*60)
    
    # Create test files
    source_dir, dest_dir, test_file = create_test_files()
    
    try:
        # Import required modules
        from forwardflow.ingest.engines.rust_high_perf.rust_high_perf_engine import (
            PyEnhancedHighPerfTransferEngine,
            CopyJob
        )
        
        print("\n1. Creating engine and job...")
        
        # Create engine
        engine = PyEnhancedHighPerfTransferEngine()
        
        # Create job with verification ENABLED
        job = CopyJob()
        job.source_paths = [source_dir]
        job.destination_paths = [dest_dir]
        job.job_id = "hash_test_job"
        job.verify_integrity = True  # ← THIS IS KEY!
        job.hash_algorithm = "sha256"  # Test with SHA-256
        
        print(f"✓ Job created with verify_integrity={job.verify_integrity}, algorithm={job.hash_algorithm}")
        
        # Set up event sink to capture events (use RustEventSink)
        from forwardflow.ingest.ui.rust_event_sink import RustEventSink
        
        events_captured = []
        
        # Create custom event sink that captures events
        class TestEventSink:
            def emit(self, event_type, payload):
                print(f"📨 EVENT: {event_type}")
                print(f"    Payload: {payload}")
                events_captured.append((event_type, payload))
                
                # Check for hash values in file.complete events
                if event_type == 'file.complete':
                    source_hash = payload.get('source_hash', 'NOT_FOUND')
                    dest_hash = payload.get('dest_hash', 'NOT_FOUND')
                    verification_passed = payload.get('verification_passed', 'NOT_FOUND')
                    print(f"    🔍 HASH VALUES:")
                    print(f"       source_hash: {source_hash}")
                    print(f"       dest_hash: {dest_hash}")
                    print(f"       verification_passed: {verification_passed}")
        
        test_sink = TestEventSink()
        engine.set_event_sink(test_sink)
        
        print("\n2. Starting file transfer...")
        
        # Run the transfer
        result = engine.copy_files(job)
        
        print(f"\n3. Transfer completed:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Files copied: {result.get('files_copied', 0)}")
        print(f"   Bytes copied: {result.get('bytes_copied', 0)}")
        print(f"   Errors: {result.get('errors', [])}")
        
        print(f"\n4. Events captured: {len(events_captured)}")
        for i, (event_type, payload) in enumerate(events_captured):
            print(f"   Event {i+1}: {event_type}")
        
        # Check if file was actually copied and hash calculated
        dest_file = Path(dest_dir) / "test.txt"
        if dest_file.exists():
            print(f"\n✓ File successfully copied to: {dest_file}")
            print(f"  Source size: {Path(test_file).stat().st_size}")
            print(f"  Dest size: {dest_file.stat().st_size}")
            
            # Calculate hash manually to verify
            import hashlib
            with open(test_file, 'rb') as f:
                source_hash_manual = hashlib.sha256(f.read()).hexdigest()
            with open(dest_file, 'rb') as f:
                dest_hash_manual = hashlib.sha256(f.read()).hexdigest()
            
            print(f"\n🔍 Manual hash verification:")
            print(f"  Source SHA-256: {source_hash_manual}")
            print(f"  Dest SHA-256: {dest_hash_manual}")
            print(f"  Hashes match: {source_hash_manual == dest_hash_manual}")
        else:
            print(f"\n❌ File was NOT copied to destination!")
        
        print("\n" + "="*60)
        print("HASH FLOW TEST COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            shutil.rmtree(Path(source_dir).parent)
            print(f"\n🧹 Cleaned up temp directory")
        except:
            pass

if __name__ == "__main__":
    test_engine_hash_flow()