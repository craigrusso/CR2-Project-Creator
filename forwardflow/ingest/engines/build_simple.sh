#!/bin/bash

# Simple build script for High Performance Transfer Engine (no CMake required)
echo "Building High Performance Transfer Engine (simple build)..."

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS, building with clang..."
    
    # Install pybind11 if not present
    if ! python3 -c "import pybind11" 2>/dev/null; then
        echo "Installing pybind11..."
        pip3 install pybind11
    fi
    
    # Get Python include path
    PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
    PYTHON_LIB=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")
    
    echo "Python include path: $PYTHON_INCLUDE"
    echo "Python lib path: $PYTHON_LIB"
    
    # Get pybind11 include path
    PYBIND11_INCLUDE=$(python3 -c "import pybind11; print(pybind11.get_include())")
    echo "pybind11 include path: $PYBIND11_INCLUDE"
    
    # Compile directly with clang
    clang++ -std=c++17 -O3 -march=native -mtune=native \
        -I"$PYTHON_INCLUDE" \
        -I"$PYBIND11_INCLUDE" \
        -shared -fPIC \
        -o high_perf_engine.so \
        high_perf_engine.cpp \
        -lpython3.12 \
        -framework CoreFoundation \
        -framework IOKit
    
    if [ $? -eq 0 ]; then
        echo "Build completed successfully!"
        echo "Generated file: high_perf_engine.so"
        ls -la high_perf_engine.so
    else
        echo "Build failed!"
        exit 1
    fi
    
else
    echo "Unsupported OS: $OSTYPE"
    echo "Please build manually using clang++ or g++"
    exit 1
fi
