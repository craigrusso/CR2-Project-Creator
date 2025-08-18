# Enhanced High-Performance File Copying Engine

A state-of-the-art file copying engine designed to saturate any available I/O pipe (1 GbE to 100 GbE, USB-C, Thunderbolt) on macOS, Windows, and Linux.

## 🚀 Features

### Core Performance Features
- **Adaptive I/O Parameters**: Automatically detects available bandwidth and optimizes block sizes, thread counts, and buffer sizes
- **Cross-Platform Direct I/O**: Bypasses OS file caches for sustained throughput with graceful fallback
- **Large Sequential Blocks**: Groups operations into 512KB-2MB blocks to minimize kernel overhead
- **Multi-Threaded Copying**: Parallel processing with range splitting for large files
- **Multi-Destination Copy**: Concurrent copying to multiple destinations with independent writer threads

### Advanced Features
- **Cryptographic Integrity Checks**: MD5, SHA-256, and xxHash64 verification with overlapping I/O
- **Network MTU Tuning**: Automatic jumbo frame detection and socket buffer optimization
- **Flexible Selection**: Support for individual files, entire folders, or custom combinations
- **Cross-Platform Abstractions**: Clean interface hiding OS-specific differences
- **Progress Monitoring**: Real-time progress reporting with detailed statistics

### Platform Optimizations
- **macOS**: Uses `F_NOCACHE` for direct I/O, optimized for APFS and HFS+
- **Windows**: Leverages `FILE_FLAG_NO_BUFFERING` and `FILE_FLAG_SEQUENTIAL_SCAN`
- **Linux**: Utilizes `O_DIRECT` with aligned buffers and `posix_fallocate`

## 📦 Installation

### Prerequisites

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install build-essential cmake libxxhash-dev libssl-dev python3-dev
```

#### CentOS/RHEL/Fedora
```bash
sudo yum install gcc-c++ cmake xxhash-devel openssl-devel python3-devel
# or for newer versions:
sudo dnf install gcc-c++ cmake xxhash-devel openssl-devel python3-devel
```

#### macOS
```bash
brew install cmake xxhash openssl
```

#### Windows
- Visual Studio 2019 or later with C++ build tools
- CMake 3.16 or later
- OpenSSL development libraries
- xxHash development libraries

### Python Dependencies
```bash
pip install -r requirements_enhanced.txt
```

### Building the C++ Engine
```bash
cd forwardflow/ingest/engines
mkdir build && cd build
cmake ..
make -j$(nproc)
```

## 🎯 Usage

### Basic Usage

```python
from forwardflow.ingest.engines.enhanced_copy_integration import copy_files

# Simple file copy
result = copy_files("source.txt", "destination.txt")

# Directory copy
result = copy_files("source_folder", "destination_folder")

# Multiple sources to multiple destinations
result = copy_files(
    ["file1.txt", "file2.txt", "folder1"],
    ["backup1/", "backup2/", "backup3/"]
)
```

### Advanced Configuration

```python
from forwardflow.ingest.engines.enhanced_copy_integration import copy_files, CopyOptions
import threading

# Create custom options
options = CopyOptions(
    block_size=2 * 1024 * 1024,  # 2MB blocks
    thread_count=16,              # 16 threads
    use_direct_io=True,           # Enable direct I/O
    verify_integrity=True,        # Enable hash verification
    hash_algorithm="xxhash64",    # Use xxHash64 for speed
    enable_jumbo_frames=True,     # Enable jumbo frames for network
    adaptive_parameters=True      # Auto-detect optimal settings
)

# Progress callback
def progress_callback(event_type, payload):
    if event_type == "file.progress":
        print(f"Progress: {payload['bytes']}/{payload['total']} bytes")

# Control events
cancel_event = threading.Event()
pause_event = threading.Event()

# Copy with custom options
result = copy_files(
    "large_file.mov",
    "backup/",
    progress_callback=progress_callback,
    cancel_event=cancel_event,
    pause_event=pause_event,
    **options.__dict__
)

print(f"Copy completed: {result.success}")
print(f"Engine used: {result.engine_used}")
print(f"Speed: {result.stats.speed_mbps:.1f} MB/s")
```

### Engine Selection

```python
from forwardflow.ingest.engines.enhanced_copy_integration import EnhancedCopyManager, CopyOptions

manager = EnhancedCopyManager()

# Force Python engine
options = CopyOptions(force_python_engine=True)
result = manager.copy_files("source", "destination", options)

# Prefer C++ engine (default)
options = CopyOptions(prefer_cpp_engine=True)
result = manager.copy_files("source", "destination", options)
```

### Bandwidth Detection

```python
from forwardflow.ingest.engines.enhanced_copy_engine import detect_bandwidth, get_optimal_copy_params

# Detect bandwidth
bandwidth = detect_bandwidth("/path/to/destination")
print(f"Read speed: {bandwidth.read_speed_mbps:.1f} MB/s")
print(f"Write speed: {bandwidth.write_speed_mbps:.1f} MB/s")

# Get optimal parameters
params = get_optimal_copy_params(bandwidth)
print(f"Optimal block size: {params['block_size']} bytes")
print(f"Optimal thread count: {params['thread_count']}")
```

## 🔧 Configuration

### Performance Tuning

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| `block_size` | I/O block size | Auto-detect | 512KB - 2MB |
| `thread_count` | Number of worker threads | Auto-detect | 1 - 64 |
| `use_direct_io` | Bypass OS cache | True | Boolean |
| `verify_integrity` | Hash verification | True | Boolean |
| `hash_algorithm` | Hash algorithm | xxhash64 | xxhash64, sha256, md5 |

### Network Optimizations

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| `mtu_size` | Network MTU size | Auto-detect | 1500 - 9000 |
| `socket_buffer_size` | Socket buffer size | Auto-detect | 64KB - 1MB |
| `enable_jumbo_frames` | Enable jumbo frames | False | Boolean |

### Adaptive Parameters

The engine automatically detects optimal settings based on:

- **Disk Speed**: SSD vs HDD, NVMe vs SATA
- **Network Speed**: 1GbE vs 10GbE vs 100GbE
- **CPU Cores**: Thread count optimization
- **Memory**: Buffer size optimization

## 📊 Performance Characteristics

### Speed Benchmarks

| Connection Type | Speed | Optimal Block Size | Threads | Expected Performance |
|----------------|-------|-------------------|---------|---------------------|
| USB 3.0 | 5 Gbps | 1MB | 4-8 | 400-500 MB/s |
| 1GbE Network | 1 Gbps | 512KB | 2-4 | 100-120 MB/s |
| 10GbE Network | 10 Gbps | 2MB | 8-16 | 1-1.2 GB/s |
| Thunderbolt 3 | 40 Gbps | 2MB | 16-32 | 3-4 GB/s |
| NVMe SSD | 7 GB/s | 2MB | 16-32 | 5-6 GB/s |

### Memory Usage

- **Small files (< 64MB)**: ~16MB buffer
- **Medium files (64MB - 1GB)**: ~256MB buffer
- **Large files (> 1GB)**: ~2GB buffer with streaming

### CPU Usage

- **Single-threaded**: 1 CPU core
- **Multi-threaded**: Scales with available cores
- **Hash verification**: Additional 1-2 cores

## 🔍 Monitoring and Debugging

### Progress Monitoring

```python
def detailed_progress_callback(event_type, payload):
    if event_type == "job.progress":
        print(f"Overall: {payload['progress_percent']:.1f}% - {payload['speed_mbps']:.1f} MB/s")
    elif event_type == "file.progress":
        print(f"File: {payload['bytes']}/{payload['total']} bytes")
    elif event_type == "file.completed":
        print(f"File completed: {payload['filename']}")
    elif event_type == "file.failed":
        print(f"File failed: {payload['error']}")

result = copy_files("source", "destination", progress_callback=detailed_progress_callback)
```

### Engine Information

```python
from forwardflow.ingest.engines.enhanced_copy_integration import get_engine_info

info = get_engine_info()
print(f"Available engines: {info['available_engines']}")
print(f"Platform: {info['platform']}")
print(f"CPU count: {info['cpu_count']}")
print(f"Bandwidth detection: {info['bandwidth_detection']}")
```

### Testing Engines

```python
from forwardflow.ingest.engines.enhanced_copy_integration import test_engines

results = test_engines()
for engine, result in results.items():
    print(f"{engine}: {'✓' if result['success'] else '✗'}")
    if result.get('stats'):
        print(f"  Speed: {result['stats']['speed_mbps']:.1f} MB/s")
```

## 🛠️ Troubleshooting

### Common Issues

#### Direct I/O Not Available
```
Error: Direct I/O not supported on this filesystem
```
**Solution**: The engine automatically falls back to buffered I/O. Performance may be reduced but functionality is maintained.

#### Insufficient Permissions
```
Error: Permission denied
```
**Solution**: Ensure write permissions on destination directory and read permissions on source files.

#### Network Performance Issues
```
Error: Network performance below expected
```
**Solution**: 
1. Check MTU settings: `ip link show`
2. Verify jumbo frame support: `ethtool -g eth0`
3. Monitor network utilization: `iftop` or `nethogs`

#### Memory Issues
```
Error: Out of memory
```
**Solution**: Reduce `block_size` or `thread_count` in CopyOptions.

### Performance Optimization

#### For High-Speed Networks (10GbE+)
```python
options = CopyOptions(
    block_size=2 * 1024 * 1024,  # 2MB blocks
    thread_count=16,              # More threads
    enable_jumbo_frames=True,     # Enable jumbo frames
    socket_buffer_size=1024 * 1024  # 1MB socket buffer
)
```

#### For Slow Networks (1GbE or slower)
```python
options = CopyOptions(
    block_size=512 * 1024,        # 512KB blocks
    thread_count=4,               # Fewer threads
    enable_jumbo_frames=False,    # Disable jumbo frames
    socket_buffer_size=256 * 1024  # 256KB socket buffer
)
```

#### For Local SSD Copying
```python
options = CopyOptions(
    block_size=2 * 1024 * 1024,  # 2MB blocks
    thread_count=32,              # Many threads
    use_direct_io=True,           # Direct I/O for SSDs
    verify_integrity=False        # Skip verification for speed
)
```

## 🔒 Security Considerations

- **Hash Verification**: Always enable for critical data transfers
- **File Permissions**: Maintain original file permissions when possible
- **Network Security**: Use encrypted connections for sensitive data
- **Memory Security**: Sensitive data in memory is cleared after use

## 📈 Future Enhancements

- **Compression**: On-the-fly compression/decompression
- **Encryption**: End-to-end encryption support
- **Resume**: Automatic resume of interrupted transfers
- **Deduplication**: Content-based deduplication
- **Cloud Integration**: Direct cloud storage support
- **GPU Acceleration**: GPU-accelerated hash calculation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the same license as the main ForwardFlow project.

## 🙏 Acknowledgments

- **xxHash**: Fast hash algorithm implementation
- **OpenSSL**: Cryptographic functions
- **pybind11**: Python-C++ bindings
- **CMake**: Cross-platform build system

---

For more information, see the main ForwardFlow documentation or contact the development team.
