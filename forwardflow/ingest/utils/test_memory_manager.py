#!/usr/bin/env python3
"""
Test script for Memory Manager
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from forwardflow.ingest.utils.memory_manager import MemoryManager, MemoryConfig

def test_memory_manager():
    """Test the memory manager functionality"""
    print("Testing Memory Manager...")
    
    try:
        # Create memory manager
        mm = MemoryManager()
        print(f"✓ Memory manager created successfully")
        print(f"  System memory: {mm.system_memory:.1f}MB")
        
        # Test available memory
        available = mm.get_available_memory()
        print(f"✓ Available memory: {available:.1f}MB")
        
        # Test different configurations
        configs = [
            ("auto", 15, True),
            ("conservative", 10, False),
            ("balanced", 20, True),
            ("aggressive", 25, False),
            ("maximum", 30, True)
        ]
        
        for preset, percent, adaptive in configs:
            config = mm.get_optimal_config(preset, percent, adaptive)
            print(f"✓ Config {preset}/{percent}%/{adaptive}:")
            print(f"    Buffer size: {config.buffer_size_mb:.1f}MB")
            print(f"    Max buffers: {config.max_concurrent_buffers}")
            print(f"    Total memory: {config.total_memory_mb:.1f}MB")
            print(f"    Available: {config.available_memory_mb:.1f}MB")
            
            # Test transfer parameters
            params = mm.get_transfer_parameters(config)
            print(f"    Transfer params: {params}")
            
            # Test memory warnings
            warning = mm.get_memory_warning(config)
            if warning:
                print(f"    Warning: {warning}")
            else:
                print(f"    No warnings")
        
        # Test memory monitoring
        stats = mm.monitor_memory_usage()
        print(f"✓ Memory stats: {stats}")
        
        # NEW: Test per-destination buffer optimization
        print("\nTesting per-destination buffer optimization:")
        test_destinations = [
            "/Volumes/USB_DRIVE/backup",
            "/Volumes/Thunderbolt_SSD/projects", 
            "smb://nas/media",
            "/Users/craigrusso/Documents",
            "/Volumes/OneDrive/cloud_storage"
        ]
        
        for dest_path in test_destinations:
            transfer_type = mm._detect_transfer_type(dest_path)
            optimal_buffer = mm.get_optimal_buffer_size_for_destination(dest_path, "auto")
            print(f"  {dest_path}: {transfer_type.upper()} → {optimal_buffer:.1f}MB buffer")
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_memory_manager()
    sys.exit(0 if success else 1)
