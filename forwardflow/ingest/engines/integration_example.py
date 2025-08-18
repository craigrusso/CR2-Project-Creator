#!/usr/bin/env python3
"""
Integration Example for Enhanced High-Performance Copy Engine

This example shows how to integrate the enhanced copy engine into the
ForwardFlow application for maximum performance.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add the parent directory to the path
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

class EnhancedCopyIntegration:
    """Integration class for using the enhanced copy engine in ForwardFlow"""
    
    def __init__(self):
        self.engine = CppEnhancedCopyEngine()
        self.bandwidth_info = None
        
    def get_system_info(self) -> dict:
        """Get system information and bandwidth"""
        if self.bandwidth_info is None:
            self.bandwidth_info = test_bandwidth()
        
        return {
            "bandwidth": self.bandwidth_info,
            "engine_available": self.engine.cpp_engine is not None,
            "platform": os.name,
            "python_version": sys.version
        }
    
    def copy_with_progress(self, source_paths: List[str], destination_paths: List[str], 
                          options: Optional[CopyOptions] = None) -> CopyStats:
        """Copy files with progress tracking"""
        
        if options is None:
            options = CopyOptions()
        
        # Progress tracking variables
        total_bytes = 0
        copied_bytes = 0
        start_time = time.time()
        
        def progress_callback(event_type: str, payload: dict):
            nonlocal copied_bytes, total_bytes
            
            if event_type == "file.progress":
                copied_bytes = payload.get("bytes", 0)
                total_bytes = payload.get("total", 0)
                
                if total_bytes > 0:
                    percentage = (copied_bytes / total_bytes) * 100
                    elapsed = time.time() - start_time
                    speed = copied_bytes / (1024 * 1024 * elapsed) if elapsed > 0 else 0
                    
                    print(f"\rProgress: {percentage:.1f}% | Speed: {speed:.2f} MB/s | "
                          f"Copied: {copied_bytes / (1024*1024):.1f} MB", end="", flush=True)
        
        # Set up progress callback
        options.progress_callback = progress_callback
        
        print(f"Starting copy operation...")
        print(f"Source(s): {source_paths}")
        print(f"Destination(s): {destination_paths}")
        
        # Perform the copy
        stats = self.engine.copy_files(source_paths, destination_paths, options)
        
        print(f"\n✓ Copy operation completed!")
        print(f"Files: {stats.copied_files}/{stats.total_files}")
        print(f"Bytes: {stats.copied_bytes}/{stats.total_bytes}")
        print(f"Speed: {stats.speed_mbps:.2f} MB/s")
        print(f"Duration: {stats.duration():.2f}s")
        
        if stats.errors:
            print(f"Errors: {len(stats.errors)}")
            for error in stats.errors:
                print(f"  - {error}")
        
        return stats
    
    def analyze_paths(self, paths: List[str]) -> dict:
        """Analyze paths to determine optimal copy parameters"""
        analysis = {
            "has_usb_tb": False,
            "has_network": False,
            "has_nvme": False,
            "recommended_settings": {}
        }
        
        for path in paths:
            if PathAnalyzer.is_usb_or_thunderbolt(path):
                analysis["has_usb_tb"] = True
            if PathAnalyzer.is_network_path(path):
                analysis["has_network"] = True
            if PathAnalyzer.is_nvme_path(path):
                analysis["has_nvme"] = True
        
        # Recommend settings based on analysis
        if analysis["has_usb_tb"]:
            analysis["recommended_settings"] = {
                "use_direct_io": False,
                "block_size": 4 * 1024 * 1024,
                "thread_count": 1,
                "verify_integrity": False
            }
        elif analysis["has_network"]:
            analysis["recommended_settings"] = {
                "use_direct_io": True,
                "block_size": 1 * 1024 * 1024,
                "thread_count": 4,
                "verify_integrity": True
            }
        elif analysis["has_nvme"]:
            analysis["recommended_settings"] = {
                "use_direct_io": "auto",
                "block_size": 4 * 1024 * 1024,
                "thread_count": 2,
                "verify_integrity": False
            }
        else:
            analysis["recommended_settings"] = {
                "use_direct_io": False,
                "block_size": 4 * 1024 * 1024,
                "thread_count": 2,
                "verify_integrity": False
            }
        
        return analysis

def example_usage():
    """Example usage of the enhanced copy engine"""
    
    print("Enhanced High-Performance Copy Engine Integration Example")
    print("=" * 60)
    
    # Initialize the integration
    integration = EnhancedCopyIntegration()
    
    # Get system information
    system_info = integration.get_system_info()
    print(f"System Information:")
    print(f"  Platform: {system_info['platform']}")
    print(f"  Python: {system_info['python_version']}")
    print(f"  C++ Engine: {'✓ Available' if system_info['engine_available'] else '✗ Not available'}")
    print(f"  Bandwidth: {system_info['bandwidth']['avg_speed']:.2f} MB/s")
    
    # Example 1: Single file copy
    print("\n" + "=" * 60)
    print("Example 1: Single File Copy")
    print("=" * 60)
    
    # Create a test file
    test_file = "test_source.txt"
    with open(test_file, 'w') as f:
        f.write("This is a test file for the enhanced copy engine.\n" * 1000)
    
    # Analyze the paths
    analysis = integration.analyze_paths([test_file, "test_dest.txt"])
    print(f"Path Analysis:")
    print(f"  USB/Thunderbolt: {analysis['has_usb_tb']}")
    print(f"  Network: {analysis['has_network']}")
    print(f"  NVMe: {analysis['has_nvme']}")
    
    # Copy with recommended settings
    recommended = analysis['recommended_settings']
    options = CopyOptions(
        use_direct_io=recommended['use_direct_io'],
        block_size=recommended['block_size'],
        thread_count=recommended['thread_count'],
        verify_integrity=recommended['verify_integrity']
    )
    
    stats = integration.copy_with_progress([test_file], ["test_dest.txt"], options)
    
    # Clean up
    os.remove(test_file)
    os.remove("test_dest.txt")
    
    # Example 2: Multiple files to multiple destinations
    print("\n" + "=" * 60)
    print("Example 2: Multiple Files to Multiple Destinations")
    print("=" * 60)
    
    # Create test files
    test_files = []
    for i in range(3):
        filename = f"test_file_{i}.txt"
        with open(filename, 'w') as f:
            f.write(f"This is test file {i}.\n" * 500)
        test_files.append(filename)
    
    # Create destination directories
    dest_dirs = ["dest1", "dest2"]
    for dest_dir in dest_dirs:
        os.makedirs(dest_dir, exist_ok=True)
    
    # Copy to multiple destinations
    dest_paths = [f"{dest_dir}/" for dest_dir in dest_dirs]
    stats = integration.copy_with_progress(test_files, dest_paths)
    
    # Clean up
    for filename in test_files:
        os.remove(filename)
    for dest_dir in dest_dirs:
        import shutil
        shutil.rmtree(dest_dir)
    
    # Example 3: Performance comparison
    print("\n" + "=" * 60)
    print("Example 3: Performance Comparison")
    print("=" * 60)
    
    # Create a larger test file
    large_file = "large_test.bin"
    file_size = 50 * 1024 * 1024  # 50MB
    
    print(f"Creating {file_size / (1024*1024):.1f} MB test file...")
    with open(large_file, 'wb') as f:
        # Write in chunks to avoid memory issues
        chunk_size = 1024 * 1024  # 1MB chunks
        for i in range(0, file_size, chunk_size):
            chunk_data = bytes([i % 256] * min(chunk_size, file_size - i))
            f.write(chunk_data)
    
    # Test different block sizes
    block_sizes = [1024 * 1024, 4 * 1024 * 1024, 8 * 1024 * 1024]  # 1MB, 4MB, 8MB
    
    for block_size in block_sizes:
        print(f"\nTesting with {block_size / (1024*1024):.0f}MB blocks...")
        
        options = CopyOptions(
            block_size=block_size,
            use_direct_io=False,  # Safe for testing
            verify_integrity=False
        )
        
        start_time = time.time()
        stats = integration.copy_with_progress([large_file], [f"copy_{block_size}.bin"], options)
        end_time = time.time()
        
        print(f"  Duration: {end_time - start_time:.2f}s")
        print(f"  Speed: {stats.speed_mbps:.2f} MB/s")
        
        # Clean up
        os.remove(f"copy_{block_size}.bin")
    
    # Clean up large test file
    os.remove(large_file)
    
    print("\n" + "=" * 60)
    print("✓ All examples completed successfully!")
    print("The enhanced copy engine is ready for production use.")

if __name__ == "__main__":
    example_usage()
