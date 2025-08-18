# Enhanced Copy Engine Integration Guide

## Overview

The enhanced copy engine is designed to be completely under the hood. You just pick your source folder and destination, and it automatically uses the best available engine.

## How to Use in ForwardFlow

### Simple Usage (Just Works!)

```python
# Import the enhanced copy functions
from forwardflow.ingest.engines.enhanced_copy_integration import copy_file, copy_files, copy_directory

# Copy a single file
stats = copy_file("source.txt", "destination.txt")

# Copy multiple files
stats = copy_files(["file1.txt", "file2.txt"], ["dest1/", "dest2/"])

# Copy a directory
stats = copy_directory("source_folder", "destination_folder")
```

### In Your ForwardFlow App

The engine automatically:
- Uses the C++ enhanced engine if available (faster)
- Falls back to standard Python if not available (still works)
- Auto-tunes parameters based on source/destination paths
- Handles USB/Thunderbolt, Network, and NVMe storage optimally

### Example Integration in ForwardFlow UI

```python
# In your copy dialog or file operation
def copy_selected_files(self):
    source_paths = self.get_selected_source_paths()
    destination_path = self.get_destination_path()
    
    # Just call the enhanced copy - it handles everything
    from forwardflow.ingest.engines.enhanced_copy_integration import copy_files
    
    stats = copy_files(source_paths, [destination_path])
    
    # Show results
    if stats.errors:
        self.show_error(f"Copy completed with {len(stats.errors)} errors")
    else:
        self.show_success(f"Copy completed: {stats.speed_mbps:.1f} MB/s")
```

## What You Get

### Automatic Performance Optimization
- **USB/Thunderbolt**: Buffered I/O, optimized for external drives
- **Network**: Direct I/O when beneficial, optimized for SMB/NFS
- **NVMe**: High-performance settings for fast storage
- **Auto-tuning**: Block sizes, thread counts, and I/O methods

### Cross-Platform Support
- **macOS**: Fast path with `clonefile` and `copyfile`
- **Windows**: Optimized for Windows file systems
- **Linux**: Direct I/O and advanced file operations

### Built-in Features
- **Progress tracking**: Real-time speed and progress
- **Error handling**: Graceful fallbacks and error reporting
- **Integrity verification**: Optional hash verification
- **Multi-destination**: Copy to multiple locations simultaneously

## No Configuration Needed

The engine is designed to "just work":
- No manual tuning required
- Automatic parameter selection
- Safe defaults for all storage types
- Fallback to standard library if enhanced engine unavailable

## Status Check

```python
from forwardflow.ingest.engines.enhanced_copy_integration import get_copy_engine_status

status = get_copy_engine_status()
print(f"Enhanced engine: {status['enhanced_engine_available']}")
print(f"C++ engine: {status['cpp_engine_available']}")
print(f"Recommended: {status['recommended_engine']}")
```

## That's It!

The enhanced copy engine is completely transparent. Just use the copy functions and get better performance automatically. No complex configuration, no manual tuning - it just works faster than the standard library.
