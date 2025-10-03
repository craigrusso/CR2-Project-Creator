#!/usr/bin/env python3
"""
Test harness for JobAggregator to validate multi-file progress behavior
"""

import sys
import os
import time
import random
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from forwardflow.ingest.ui.job_aggregator import JobAggregator, JobSnapshot


def simulate_multi_file_transfer():
    """Simulate a multi-file transfer to test JobAggregator behavior"""
    print("=== JobAggregator Multi-File Transfer Simulation ===")
    
    # Test parameters
    total_files = 64
    destinations = [
        "/Users/test/Desktop/TEST_TRANSFER_1",
        "/Users/test/Desktop/TEST_TRANSFER_2"
    ]
    
    # File simulation data (file_id, total_bytes, dest_index)
    test_files = []
    for i in range(total_files):
        file_id = f"file_{i:03d}.mov"
        total_bytes = random.randint(1024*1024, 1024*1024*1024)  # 1MB to 1GB
        dest_index = i % len(destinations)  # Alternate between destinations
        test_files.append((file_id, total_bytes, destinations[dest_index]))
    
    # Initialize JobAggregator
    aggregator = JobAggregator(total_files, destinations)
    print(f"Initialized JobAggregator for {total_files} files to {len(destinations)} destinations")
    
    # Test 1: Sequential file progress updates
    print("\n--- Test 1: Sequential File Progress Updates ---")
    for i, (file_id, total_bytes, dest_path) in enumerate(test_files[:5]):
        print(f"\nFile {i+1}: {file_id} ({total_bytes/1024/1024:.1f} MB)")
        
        # Simulate progressive copy
        for progress in [0.25, 0.5, 0.75, 1.0]:
            bytes_copied = int(total_bytes * progress)
            snapshot = aggregator.update_file_progress(file_id, bytes_copied, total_bytes, dest_path, file_id)
            
            print(f"  Progress {progress*100:.0f}%: Job {snapshot.job_progress_percent:.1f}% "
                  f"({snapshot.job_completed_files}/{snapshot.job_total_files} files) "
                  f"Speed: {snapshot.job_current_mb_s:.1f} MB/s")
        
        # Small delay to simulate real transfer timing
        time.sleep(0.01)
    
    # Test 2: Verify monotonic progress
    print("\n--- Test 2: Monotonic Progress Verification ---")
    last_progress = 0.0
    monotonic_pass = True
    
    for i, (file_id, total_bytes, dest_path) in enumerate(test_files[5:15]):
        bytes_copied = total_bytes  # Complete the file immediately
        snapshot = aggregator.update_file_progress(file_id, bytes_copied, total_bytes, dest_path, file_id)
        
        if snapshot.job_progress_percent < last_progress:
            print(f"  FAIL: Progress regressed from {last_progress:.1f}% to {snapshot.job_progress_percent:.1f}%")
            monotonic_pass = False
        
        last_progress = snapshot.job_progress_percent
        print(f"  File {i+6}: Progress {snapshot.job_progress_percent:.1f}% (monotonic: OK)")
    
    print(f"\nMonotonic Progress Test: {'PASS' if monotonic_pass else 'FAIL'}")
    
    # Test 3: Per-destination metrics
    print("\n--- Test 3: Per-Destination Metrics ---")
    current_snapshot = aggregator.get_current_snapshot()
    
    for dest_path, dest_metrics in current_snapshot.destinations.items():
        print(f"  Destination: {dest_path}")
        print(f"    Files: {dest_metrics.completed_files}/{dest_metrics.total_files}")
        print(f"    Bytes: {dest_metrics.bytes_copied/1024/1024:.1f} MB / {dest_metrics.total_bytes/1024/1024:.1f} MB")
        print(f"    Speed: Current {dest_metrics.current_mb_s:.1f} MB/s, Peak {dest_metrics.peak_mb_s:.1f} MB/s")
    
    # Test 4: Speed calculations
    print("\n--- Test 4: Speed Calculation Validation ---")
    speed_test_pass = True
    
    if current_snapshot.job_peak_mb_s < current_snapshot.job_current_mb_s:
        print("  FAIL: Peak speed is less than current speed")
        speed_test_pass = False
    
    if current_snapshot.job_avg_mb_s <= 0:
        print("  FAIL: Average speed is zero or negative")
        speed_test_pass = False
    
    if current_snapshot.job_current_mb_s < 0:
        print("  FAIL: Current speed is negative")
        speed_test_pass = False
    
    print(f"  Current Speed: {current_snapshot.job_current_mb_s:.1f} MB/s")
    print(f"  Average Speed: {current_snapshot.job_avg_mb_s:.1f} MB/s")
    print(f"  Peak Speed: {current_snapshot.job_peak_mb_s:.1f} MB/s")
    print(f"\nSpeed Calculation Test: {'PASS' if speed_test_pass else 'FAIL'}")
    
    # Test 5: File count accuracy
    print("\n--- Test 5: File Count Accuracy ---")
    files_processed = len([f for f in test_files[:15]])  # We processed 15 files
    
    count_test_pass = (
        current_snapshot.job_total_files == total_files and
        current_snapshot.job_completed_files == files_processed
    )
    
    print(f"  Expected Total Files: {total_files}")
    print(f"  Actual Total Files: {current_snapshot.job_total_files}")
    print(f"  Expected Completed Files: {files_processed}")
    print(f"  Actual Completed Files: {current_snapshot.job_completed_files}")
    print(f"\nFile Count Test: {'PASS' if count_test_pass else 'FAIL'}")
    
    # Test 6: ETA reasonableness
    print("\n--- Test 6: ETA Reasonableness ---")
    eta_test_pass = True
    
    if current_snapshot.job_eta_seconds < 0:
        print("  FAIL: ETA is negative")
        eta_test_pass = False
    
    if current_snapshot.job_progress_percent >= 100 and current_snapshot.job_eta_seconds > 0:
        print("  FAIL: ETA > 0 when job is 100% complete")
        eta_test_pass = False
    
    print(f"  ETA: {current_snapshot.job_eta_seconds:.1f} seconds")
    print(f"  Progress: {current_snapshot.job_progress_percent:.1f}%")
    print(f"\nETA Test: {'PASS' if eta_test_pass else 'FAIL'}")
    
    # Final Summary
    print("\n=== Test Summary ===")
    all_tests_pass = monotonic_pass and speed_test_pass and count_test_pass and eta_test_pass
    
    print(f"Monotonic Progress: {'PASS' if monotonic_pass else 'FAIL'}")
    print(f"Speed Calculations: {'PASS' if speed_test_pass else 'FAIL'}")
    print(f"File Count Accuracy: {'PASS' if count_test_pass else 'FAIL'}")
    print(f"ETA Reasonableness: {'PASS' if eta_test_pass else 'FAIL'}")
    print(f"\nOverall Result: {'PASS' if all_tests_pass else 'FAIL'}")
    
    return all_tests_pass


def test_edge_cases():
    """Test edge cases that might cause issues"""
    print("\n=== Edge Case Testing ===")
    
    # Test with zero files
    print("\n--- Test: Zero Files ---")
    try:
        aggregator = JobAggregator(0, ["/test/dest"])
        snapshot = aggregator.get_current_snapshot()
        print(f"Zero files test: PASS (progress: {snapshot.job_progress_percent:.1f}%)")
    except Exception as e:
        print(f"Zero files test: FAIL - {e}")
    
    # Test with empty destinations
    print("\n--- Test: Empty Destinations ---")
    try:
        aggregator = JobAggregator(10, [])
        snapshot = aggregator.get_current_snapshot()
        print(f"Empty destinations test: PASS (no crash)")
    except Exception as e:
        print(f"Empty destinations test: FAIL - {e}")
    
    # Test with duplicate file updates
    print("\n--- Test: Duplicate File Updates ---")
    try:
        aggregator = JobAggregator(1, ["/test/dest"])
        
        # Update same file multiple times
        aggregator.update_file_progress("duplicate_file", 512, 1024, "/test/dest", "test.txt")
        snapshot1 = aggregator.get_current_snapshot()
        
        aggregator.update_file_progress("duplicate_file", 1024, 1024, "/test/dest", "test.txt") 
        snapshot2 = aggregator.get_current_snapshot()
        
        if snapshot2.job_progress_percent >= snapshot1.job_progress_percent:
            print("Duplicate updates test: PASS (progress didn't regress)")
        else:
            print("Duplicate updates test: FAIL (progress regressed)")
    except Exception as e:
        print(f"Duplicate updates test: FAIL - {e}")


if __name__ == "__main__":
    print("Running JobAggregator Test Harness...")
    
    # Run main simulation
    main_pass = simulate_multi_file_transfer()
    
    # Run edge case tests
    test_edge_cases()
    
    print("\n" + "="*50)
    print("JobAggregator Test Harness Complete")
    print(f"Main Tests: {'PASS' if main_pass else 'FAIL'}")
    print("="*50)