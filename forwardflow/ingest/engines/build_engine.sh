#!/bin/bash

# Build script for High Performance Transfer Engine
echo "Building High Performance Transfer Engine..."

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS, building with clang..."
    
    # Install pybind11 if not present
    if ! python3 -c "import pybind11" 2>/dev/null; then
        echo "Installing pybind11..."
        pip3 install pybind11
    fi
    
    # Create build directory
    mkdir -p build
    cd build
    
    # Configure with CMake
    cmake .. -DCMAKE_BUILD_TYPE=Release
    
    # Build
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    
    # Copy the built module
    cp high_perf_engine.* ../
    
    echo "Build completed successfully!"
    echo "Generated files:"
    ls -la ../high_perf_engine.*
    
else
    echo "Unsupported OS: $OSTYPE"
    echo "Please build manually using CMake"
    exit 1
fi
