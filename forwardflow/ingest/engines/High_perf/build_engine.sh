#!/bin/bash

# Build script for the modular ForwardFlow High-Performance Engine
# This script builds the engine with cloud-aware and stall-safe features

set -e

echo "Building ForwardFlow High-Performance Engine (Modular)..."
echo "========================================================"

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS - building with cloud storage support"
    PLATFORM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux - building with network storage support"
    PLATFORM="linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "Detected Windows - building with Windows-specific optimizations"
    PLATFORM="windows"
else
    echo "Unknown platform: $OSTYPE"
    exit 1
fi

# Create build directory
BUILD_DIR="build_modular"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with CMake
echo "Configuring with CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build the engine
echo "Building the engine..."
make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# Check if build was successful
if [ -f "../enhanced_high_perf_engine.cpython-312-darwin.so" ]; then
    echo "Build successful!"
    echo "Output files:"
    ls -la ../enhanced_high_perf_engine.cpython-312-darwin.so
    
    # Copy the built engine to the build/lib directory where Python expects it
    echo "Copying engine to build/lib directory..."
    mkdir -p ../build/lib
    cp ../enhanced_high_perf_engine.cpython-312-darwin.so ../build/lib/
    echo "✓ Engine copied to build/lib directory"
    
    echo "Engine built successfully and copied to build/lib directory"
else
    echo "Build failed - no output files found"
    echo "Current directory: $(pwd)"
    echo "Engines directory contents:"
    ls -la ../
    exit 1
fi

echo "========================================================"
echo "Build completed successfully!"
echo ""
echo "The modular engine now includes:"
echo "- Cloud storage detection and materialization"
echo "- Stall watchdog for file operations"
echo "- Improved error handling and reporting"
echo "- Clean, organized code structure"
echo ""
echo "New folder structure:"
echo "High_perf/"
echo "├── cloud/           - Cloud storage handling"
echo "├── stall/           - Stall detection"
echo "├── platform/        - Platform-specific optimizations"
echo "├── io/              - Cross-platform I/O operations"
echo "├── verification/    - Verification and reporting"
echo "├── core/            - Core engine functionality"
echo "└── enhanced_engine_main.cpp - Main entry point"
echo ""
echo "Each module is focused and under 200 lines for maintainability"
