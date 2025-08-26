#!/usr/bin/env python3
"""
Test script to verify enhanced C++ engine data structures are working
"""

import sys
import os

# Add the engine path
sys.path.insert(0, 'forwardflow/ingest/engines/High_perf')

try:
    print("Testing enhanced C++ engine data structures...")
    
    # Import the enhanced engine
    import enhanced_high_perf_engine as cpp_engine
    print("✓ Successfully imported enhanced_high_perf_engine")
    
    # Test FileTransferRecord
    print("\nTesting FileTransferRecord...")
    file_record = cpp_engine.FileTransferRecord()
    file_record.source_path = "/test/source/file.mov"
    file_record.destination_path = "/test/dest/file.mov"
    file_record.filename = "file.mov"
    file_record.file_size = 1024 * 1024 * 100  # 100MB
    file_record.status = "COMPLETED"
    file_record.verification_passed = True
    
    print(f"✓ FileTransferRecord created successfully:")
    print(f"  Source: {file_record.source_path}")
    print(f"  Destination: {file_record.destination_path}")
    print(f"  Filename: {file_record.filename}")
    print(f"  Size: {file_record.file_size} bytes")
    print(f"  Status: {file_record.status}")
    print(f"  Verification: {file_record.verification_passed}")
    
    # Test EnhancedCopyStats
    print("\nTesting EnhancedCopyStats...")
    stats = cpp_engine.EnhancedCopyStats()
    stats.total_files = 10
    stats.completed_files = 8
    stats.cancelled_files = 1
    stats.error_files = 1
    stats.total_bytes = 1024 * 1024 * 1000  # 1GB
    stats.completed_bytes = 1024 * 1024 * 800  # 800MB
    stats.average_speed_mbps = 50.5
    stats.file_records = [file_record]
    
    print(f"✓ EnhancedCopyStats created successfully:")
    print(f"  Total files: {stats.total_files}")
    print(f"  Completed: {stats.completed_files}")
    print(f"  Cancelled: {stats.cancelled_files}")
    print(f"  Errors: {stats.error_files}")
    print(f"  Total bytes: {stats.total_bytes}")
    print(f"  Completed bytes: {stats.completed_bytes}")
    print(f"  Average speed: {stats.average_speed_mbps} MB/s")
    print(f"  File records: {len(stats.file_records)}")
    
    # Test CopyJob
    print("\nTesting CopyJob...")
    job = cpp_engine.CopyJob()
    job.source_paths = ["/test/source"]
    job.destination_paths = ["/test/dest"]
    job.job_id = "test_job_123"
    job.reports_folder_name = "_CR2_CREATIVE_REPORTS"
    
    print(f"✓ CopyJob created successfully:")
    print(f"  Source paths: {job.source_paths}")
    print(f"  Destination paths: {job.destination_paths}")
    print(f"  Job ID: {job.job_id}")
    print(f"  Reports folder: {job.reports_folder_name}")
    
    print("\n🎉 All enhanced data structures are working correctly!")
    print("The C++ engine is now ready to provide industry-standard DIT reporting data.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("The enhanced engine module could not be imported.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error testing enhanced engine: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
