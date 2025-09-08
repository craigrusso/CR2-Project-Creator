# Rust High Performance Engine

This is a high-performance file transfer engine written in Rust, designed to replace the C++ implementation in ForwardFlow with better performance and cross-platform support.

## Features

- **High Performance**: Optimized for maximum transfer speeds
- **Cross-Platform**: Windows, macOS, and Linux support
- **Parallel Processing**: Multi-threaded file operations
- **Progress Tracking**: Real-time progress updates and statistics
- **Verification**: Hash-based integrity checking
- **Cloud Detection**: Automatic cloud storage detection
- **Python Integration**: Full PyO3 bindings for Python integration

## Architecture

The engine is organized into modular components, each under 300 lines as per project requirements:

- **`data_structures.rs`**: Core data types and structures
- **`engine_core.rs`**: Main engine implementation and orchestration
- **`file_operations.rs`**: File I/O and parallel processing
- **`verification.rs`**: Hash verification and integrity checking
- **`progress_tracking.rs`**: Progress monitoring and statistics
- **`cloud_detection.rs`**: Cloud storage detection and handling
- **`platform_helpers.rs`**: Cross-platform utilities
- **`event_system.rs`**: Python callback and event system

## Building

### Prerequisites

1. **Rust**: Install Rust using [rustup](https://rustup.rs/)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source "$HOME/.cargo/env"
   ```

2. **Python**: Python 3.8+ with development headers
   - **macOS**: `brew install python`
   - **Ubuntu/Debian**: `sudo apt-get install python3-dev`
   - **Windows**: Install from python.org

### Build Commands

1. **Development Build**:
   ```bash
   cd forwardflow/ingest/engines/rust_high_perf
   cargo build
   ```

2. **Release Build** (Optimized):
   ```bash
   cargo build --release
   ```

3. **Cross-Platform Build**:
   ```bash
   # For macOS ARM64
   cargo build --release --target aarch64-apple-darwin
   
   # For macOS Intel
   cargo build --release --target x86_64-apple-darwin
   
   # For Linux
   cargo build --release --target x86_64-unknown-linux-gnu
   
   # For Windows
   cargo build --release --target x86_64-pc-windows-msvc
   ```

## Python Integration

The engine provides a Python module that can be imported and used directly:

```python
import rust_high_perf_engine

# Create engine instance
engine = rust_high_perf_engine.PyEnhancedHighPerfTransferEngine()

# Set up event sink for progress updates
def event_handler(event_type, payload):
    print(f"Event: {event_type}, Payload: {payload}")

engine.set_event_sink(event_handler)

# Create copy job
from rust_high_perf_engine import CopyJob
job = CopyJob()
job.source_paths = ["/path/to/source"]
job.destination_paths = ["/path/to/destination"]
job.job_id = "test_job_001"

# Execute copy operation
stats = engine.copy_files(job)
print(f"Copy completed: {stats.copied_files} files, {stats.copied_bytes} bytes")
```

## Performance Characteristics

- **Buffer Sizes**: Adaptive buffer sizing (64KB to 16MB) based on file size
- **Parallelism**: Configurable parallel workers for file operations
- **Memory Management**: Efficient memory usage with minimal allocations
- **I/O Optimization**: Optimized for both small and large files

## Platform-Specific Features

### Windows
- Native Windows API integration
- Optimized for NTFS performance
- Support for Windows-specific file attributes

### macOS
- Core Foundation integration
- Optimized for APFS and HFS+
- Native macOS file system features

### Linux
- POSIX-compliant implementation
- Support for various file systems (ext4, btrfs, etc.)
- Linux-specific optimizations

## Error Handling

The engine provides comprehensive error handling:
- Disk space validation
- File permission checks
- Network error recovery
- Integrity verification failures

## Testing

Run the test suite:

```bash
cargo test
```

Run specific tests:

```bash
cargo test --test data_structures
cargo test --test engine_core
```

## Troubleshooting

### Common Build Issues

1. **PyO3 Build Errors**:
   - Ensure Python development headers are installed
   - Check Python version compatibility (3.8+)
   - Verify `PYTHON_SYS_EXECUTABLE` environment variable

2. **Platform-Specific Dependencies**:
   - **macOS**: Install Xcode Command Line Tools
   - **Linux**: Install build essentials (`build-essential`)
   - **Windows**: Install Visual Studio Build Tools

3. **Memory Issues**:
   - Reduce parallel worker count
   - Adjust buffer sizes
   - Monitor system memory usage

### Performance Issues

1. **Slow Transfer Speeds**:
   - Check disk I/O performance
   - Verify network bandwidth (for network destinations)
   - Adjust buffer sizes and parallelism

2. **High Memory Usage**:
   - Reduce buffer sizes
   - Limit parallel operations
   - Monitor system resources

## Contributing

When contributing to the engine:

1. **Code Organization**: Keep files under 300 lines
2. **Performance**: Focus on performance-critical paths
3. **Cross-Platform**: Ensure compatibility across platforms
4. **Testing**: Add tests for new functionality
5. **Documentation**: Update this README for new features

## License

This engine is part of the ForwardFlow project and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the test suite for usage examples
3. Check the Python integration examples
4. Review the C++ engine implementation for reference

