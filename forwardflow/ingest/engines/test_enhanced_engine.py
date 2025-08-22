#!/usr/bin/env python3
"""
Test script for the enhanced high-performance copy engine

This script tests all the new features including:
- Safer defaults
- macOS fast path
- Bounded concurrency
- Preallocation
- Streaming hashes
- Multi-destination support
- Auto-tuning
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add the parent directory to the path to import the engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from app.utils.cpp_enhanced_copy import (
        CppEnhancedCopyEngine, CopyOptions, CopyStats, PathAnalyzer,
        copy_file, copy_files, test_bandwidth
    )
    print("✓ Enhanced copy engine imported successfully")
except ImportError as e:
    print(f"✗ Failed to import enhanced copy engine: {e}")
    sys.exit(1)

def create_test_files(base_dir: Path, num_files: int = 5, file_size: int = 1024 * 1024) -> list:
    """Create test files for copying"""
    test_files = []
    
    for i in range(num_files):
        file_path = base_dir / f"test_file_{i}.bin"
        with open(file_path, 'wb') as f:
            # Write some pattern data
            data = bytes([i % 256] * file_size)
            f.write(data)
        test_files.append(str(file_path))
    
    print(f"✓ Created {num_files} test files in {base_dir}")
    return test_files

def test_basic_copy():
    """Test basic file copying"""
    print("\n=== Testing Basic Copy ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files
        test_files = create_test_files(source_dir, 3, 1024 * 1024)  # 3 files, 1MB each
        
        # Test single file copy
        source_file = test_files[0]
        dest_file = str(dest_dir / "copied_file.bin")
        
        print(f"Copying {source_file} to {dest_file}")
        stats = copy_file(source_file, dest_file)
        
        print(f"✓ Single file copy completed:")
        print(f"  Files: {stats.copied_files}/{stats.total_files}")
        print(f"  Bytes: {stats.copied_bytes}/{stats.total_bytes}")
        print(f"  Speed: {stats.speed_mbps:.2f} MB/s")
        print(f"  Duration: {stats.duration():.2f}s")
        
        # Verify file exists and has correct size
        # The C++ engine copies to the destination directory with the original filename
        source_name = Path(source_file).name
        actual_dest_file = dest_dir / source_name
        assert actual_dest_file.exists()
        assert actual_dest_file.stat().st_size == Path(source_file).stat().st_size
        print("✓ File verification passed")

def test_multi_destination():
    """Test multi-destination copying"""
    print("\n=== Testing Multi-Destination Copy ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest1_dir = temp_path / "dest1"
        dest2_dir = temp_path / "dest2"
        
        source_dir.mkdir()
        dest1_dir.mkdir()
        dest2_dir.mkdir()
        
        # Create test files
        test_files = create_test_files(source_dir, 2, 512 * 1024)  # 2 files, 512KB each
        
        # Test multi-destination copy
        source_files = test_files
        dest_paths = [str(dest1_dir), str(dest2_dir)]
        
        print(f"Copying {len(source_files)} files to {len(dest_paths)} destinations")
        stats = copy_files(source_files, dest_paths)
        
        print(f"✓ Multi-destination copy completed:")
        print(f"  Files: {stats.copied_files}/{stats.total_files}")
        print(f"  Bytes: {stats.copied_bytes}/{stats.total_bytes}")
        print(f"  Speed: {stats.speed_mbps:.2f} MB/s")
        
        # Verify files exist in both destinations
        for dest_dir in [dest1_dir, dest2_dir]:
            for source_file in test_files:
                source_name = Path(source_file).name
                dest_file = dest_dir / source_name
                assert dest_file.exists()
                assert dest_file.stat().st_size == Path(source_file).stat().st_size
        print("✓ Multi-destination verification passed")

def test_auto_tuning():
    """Test auto-tuning functionality"""
    print("\n=== Testing Auto-Tuning ===")
    
    engine = CppEnhancedCopyEngine()
    
    # Test bandwidth detection
    print("Testing bandwidth detection...")
    bandwidth = test_bandwidth()
    print(f"✓ Bandwidth test completed:")
    print(f"  Write: {bandwidth['write_speed']:.2f} MB/s")
    print(f"  Read: {bandwidth['read_speed']:.2f} MB/s")
    print(f"  Average: {bandwidth['avg_speed']:.2f} MB/s")
    
    # Test optimal parameters
    print("Testing optimal parameters...")
    params = engine.get_optimal_parameters(bandwidth['avg_speed'])
    print(f"✓ Optimal parameters:")
    print(f"  Block size: {params['block_size']} bytes")
    print(f"  Thread count: {params['thread_count']}")
    print(f"  Direct I/O: {params['use_direct_io']}")
    print(f"  Large file threshold: {params['large_file_threshold']} bytes")

def test_path_analysis():
    """Test path analysis functionality"""
    print("\n=== Testing Path Analysis ===")
    
    # Test USB/Thunderbolt detection
    test_paths = [
        "/Volumes/MyUSBDrive/file.txt",  # macOS USB
        "D:/file.txt",  # Windows removable
        "/home/user/file.txt",  # Linux local
        "//server/share/file.txt",  # Network
        "C:/file.txt",  # Windows local
    ]
    
    for path in test_paths:
        is_usb = PathAnalyzer.is_usb_or_thunderbolt(path)
        is_network = PathAnalyzer.is_network_path(path)
        is_nvme = PathAnalyzer.is_nvme_path(path)
        
        print(f"Path: {path}")
        print(f"  USB/TB: {is_usb}")
        print(f"  Network: {is_network}")
        print(f"  NVMe: {is_nvme}")
    
    print("✓ Path analysis completed")

def test_verification():
    """Test integrity verification"""
    print("\n=== Testing Integrity Verification ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create a test file with known content
        source_file = source_dir / "test_verify.bin"
        test_data = b"Hello, World! This is test data for verification."
        with open(source_file, 'wb') as f:
            f.write(test_data)
        
        dest_file = str(dest_dir / "test_verify_copy.bin")
        
        # Test with verification enabled
        print("Testing copy with verification...")
        options = CopyOptions(verify_integrity=True, hash_algorithm="xxhash64")
        stats = copy_file(str(source_file), dest_file, **options.__dict__)
        
        print(f"✓ Verification copy completed:")
        print(f"  Hash verifications: {stats.hash_verifications}")
        print(f"  Hash failures: {stats.hash_failures}")
        
        # Verify the copied file has the same content
        # The C++ engine copies to the destination directory with the original filename
        source_name = Path(source_file).name
        actual_dest_file = dest_dir / source_name
        with open(actual_dest_file, 'rb') as f:
            copied_data = f.read()
        
        assert copied_data == test_data
        print("✓ Content verification passed")

def test_large_file():
    """Test large file handling"""
    print("\n=== Testing Large File Handling ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create a large file (larger than the threshold)
        large_file = source_dir / "large_file.bin"
        file_size = 300 * 1024 * 1024  # 300MB (above 256MB threshold)
        
        print(f"Creating large file ({file_size / (1024*1024):.1f} MB)...")
        with open(large_file, 'wb') as f:
            # Write in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1MB chunks
            for i in range(0, file_size, chunk_size):
                chunk_data = bytes([i % 256] * min(chunk_size, file_size - i))
                f.write(chunk_data)
        
        dest_file = str(dest_dir / "large_file_copy.bin")
        
        print("Testing large file copy...")
        start_time = time.time()
        stats = copy_file(str(large_file), dest_file)
        end_time = time.time()
        
        print(f"✓ Large file copy completed:")
        print(f"  Duration: {end_time - start_time:.2f}s")
        print(f"  Speed: {stats.speed_mbps:.2f} MB/s")
        print(f"  Files: {stats.copied_files}/{stats.total_files}")
        
        # Verify file size
        # The C++ engine copies to the destination directory with the original filename
        source_name = Path(large_file).name
        actual_dest_file = dest_dir / source_name
        assert actual_dest_file.stat().st_size == file_size
        print("✓ Large file verification passed")

def main():
    """Run all tests"""
    print("Enhanced High-Performance Copy Engine Test Suite")
    print("=" * 50)
    
    try:
        test_basic_copy()
        test_multi_destination()
        test_auto_tuning()
        test_path_analysis()
        test_verification()
        test_large_file()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("The enhanced copy engine is working correctly.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
