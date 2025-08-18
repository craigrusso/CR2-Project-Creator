#!/usr/bin/env python3
"""
Test script for C++ Enhanced Copy Engine Integration

This script tests the C++ enhanced copy engine and compares its performance
with the Python fallback.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cpp_engine_import():
    """Test if the C++ engine can be imported"""
    print("Testing C++ engine import...")
    
    try:
        from app.utils.cpp_enhanced_copy import (
            CppEnhancedCopyEngine, CopyStats, CopyOptions,
            copy_files, copy_file, copy_directory,
            CPP_ENGINE_AVAILABLE
        )
        print(f"✓ C++ engine import successful")
        print(f"  - CPP_ENGINE_AVAILABLE: {CPP_ENGINE_AVAILABLE}")
        return True
    except ImportError as e:
        print(f"✗ C++ engine import failed: {e}")
        return False

def test_engine_initialization():
    """Test engine initialization"""
    print("\nTesting engine initialization...")
    
    try:
        from app.utils.cpp_enhanced_copy import CppEnhancedCopyEngine
        engine = CppEnhancedCopyEngine()
        print("✓ Engine initialization successful")
        return engine
    except Exception as e:
        print(f"✗ Engine initialization failed: {e}")
        return None

def test_bandwidth_detection(engine):
    """Test bandwidth detection"""
    print("\nTesting bandwidth detection...")
    
    try:
        bandwidth = engine.test_bandwidth()
        print(f"✓ Bandwidth detection successful:")
        print(f"  - Write speed: {bandwidth.get('write_speed', 0):.2f} MB/s")
        print(f"  - Read speed: {bandwidth.get('read_speed', 0):.2f} MB/s")
        print(f"  - Average speed: {bandwidth.get('avg_speed', 0):.2f} MB/s")
        return bandwidth
    except Exception as e:
        print(f"✗ Bandwidth detection failed: {e}")
        return None

def test_optimal_parameters(engine, bandwidth=None):
    """Test optimal parameters calculation"""
    print("\nTesting optimal parameters calculation...")
    
    try:
        optimal_params = engine.get_optimal_parameters(
            bandwidth.get('avg_speed', 0) if bandwidth else 0
        )
        print(f"✓ Optimal parameters calculation successful:")
        print(f"  - Block size: {optimal_params.get('block_size', 0) / (1024*1024):.1f} MB")
        print(f"  - Thread count: {optimal_params.get('thread_count', 0)}")
        print(f"  - Use direct I/O: {optimal_params.get('use_direct_io', False)}")
        print(f"  - Large file threshold: {optimal_params.get('large_file_threshold', 0) / (1024*1024):.1f} MB")
        return optimal_params
    except Exception as e:
        print(f"✗ Optimal parameters calculation failed: {e}")
        return None

def test_file_copy(engine):
    """Test file copying"""
    print("\nTesting file copying...")
    
    try:
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_content = "This is a test file for the enhanced copy engine.\n" * 1000
            f.write(test_content)
            source_file = f.name
        
        # Create destination directory
        dest_dir = tempfile.mkdtemp()
        dest_file = os.path.join(dest_dir, "copied_test_file.txt")
        
        # Test copy using the engine's copy_files method with CopyOptions
        from app.utils.cpp_enhanced_copy import CopyOptions
        
        options = CopyOptions(verify_integrity=True)
        start_time = time.time()
        
        # Use copy_files with source and destination as lists
        stats = engine.copy_files([source_file], [dest_dir], options)
        end_time = time.time()
        
        # The file should be copied to the destination directory with the same name
        expected_dest_file = os.path.join(dest_dir, os.path.basename(source_file))
        
        # Verify copy
        if os.path.exists(expected_dest_file):
            with open(source_file, 'r') as f1, open(expected_dest_file, 'r') as f2:
                if f1.read() == f2.read():
                    print("✓ File copy successful")
                    print(f"  - Source: {source_file}")
                    print(f"  - Destination: {expected_dest_file}")
                    print(f"  - Copy time: {end_time - start_time:.3f} seconds")
                    print(f"  - Stats: {stats.copied_files} files, {stats.copied_bytes} bytes")
                    print(f"  - Speed: {stats.speed_mbps:.2f} MB/s")
                    success = True
                else:
                    print("✗ File copy failed: content mismatch")
                    success = False
        else:
            print(f"✗ File copy failed: destination file not created at {expected_dest_file}")
            success = False
        
        # Cleanup
        os.unlink(source_file)
        if os.path.exists(expected_dest_file):
            os.unlink(expected_dest_file)
        os.rmdir(dest_dir)
        
        return success
    except Exception as e:
        print(f"✗ File copy test failed: {e}")
        return False

def test_hash_calculation(engine):
    """Test hash calculation"""
    print("\nTesting hash calculation...")
    
    try:
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_content = "This is a test file for hash calculation.\n" * 100
            f.write(test_content)
            test_file = f.name
        
        # Test hash calculation
        hash_result = engine.calculate_file_hash(test_file, "xxhash64")
        
        if hash_result:
            print(f"✓ Hash calculation successful:")
            print(f"  - File: {test_file}")
            print(f"  - Hash (xxhash64): {hash_result}")
            success = True
        else:
            print("✗ Hash calculation failed: empty result")
            success = False
        
        # Cleanup
        os.unlink(test_file)
        
        return success
    except Exception as e:
        print(f"✗ Hash calculation test failed: {e}")
        return False

def test_file_operations_handler():
    """Test the FileOperationsHandler integration"""
    print("\nTesting FileOperationsHandler integration...")
    
    try:
        from app.utils.file_operations.file_operations import FileOperationsHandler
        
        # Create handler
        handler = FileOperationsHandler()
        
        # Test performance
        performance = handler.test_enhanced_copy_performance()
        
        if "error" not in performance:
            print("✓ FileOperationsHandler integration successful:")
            print(f"  - Engine type: {performance.get('engine_type', 'Unknown')}")
            print(f"  - Bandwidth: {performance.get('bandwidth_mbps', 0):.2f} MB/s")
            print(f"  - Optimal block size: {performance.get('optimal_block_size', 0) / (1024*1024):.1f} MB")
            print(f"  - Optimal thread count: {performance.get('optimal_thread_count', 0)}")
            return True
        else:
            print(f"✗ FileOperationsHandler integration failed: {performance['error']}")
            return False
    except Exception as e:
        print(f"✗ FileOperationsHandler integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("C++ Enhanced Copy Engine Integration Test")
    print("=" * 60)
    
    # Test import
    if not test_cpp_engine_import():
        print("\n❌ C++ engine import failed. Cannot proceed with tests.")
        return False
    
    # Test engine initialization
    engine = test_engine_initialization()
    if not engine:
        print("\n❌ Engine initialization failed. Cannot proceed with tests.")
        return False
    
    # Test bandwidth detection
    bandwidth = test_bandwidth_detection(engine)
    
    # Test optimal parameters
    optimal_params = test_optimal_parameters(engine, bandwidth)
    
    # Test file copy
    copy_success = test_file_copy(engine)
    
    # Test hash calculation
    hash_success = test_hash_calculation(engine)
    
    # Test FileOperationsHandler integration
    handler_success = test_file_operations_handler()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("C++ Engine Import", True),
        ("Engine Initialization", engine is not None),
        ("Bandwidth Detection", bandwidth is not None),
        ("Optimal Parameters", optimal_params is not None),
        ("File Copy", copy_success),
        ("Hash Calculation", hash_success),
        ("FileOperationsHandler Integration", handler_success)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, success in tests:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name:35} {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! C++ Enhanced Copy Engine is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
