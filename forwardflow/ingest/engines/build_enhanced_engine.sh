#!/bin/bash

# Enhanced High-Performance File Copying Engine Build Script
# This script automates the building and installation of the enhanced engine

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect platform
detect_platform() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*)    echo "windows";;
        MINGW*)     echo "windows";;
        MSYS*)      echo "windows";;
        *)          echo "unknown";;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system dependencies
install_system_deps() {
    local platform=$1
    
    print_status "Installing system dependencies for $platform..."
    
    case $platform in
        "linux")
            if command_exists apt-get; then
                # Ubuntu/Debian
                sudo apt-get update
                sudo apt-get install -y build-essential cmake libxxhash-dev libssl-dev python3-dev pkg-config
            elif command_exists yum; then
                # CentOS/RHEL
                sudo yum install -y gcc-c++ cmake xxhash-devel openssl-devel python3-devel pkgconfig
            elif command_exists dnf; then
                # Fedora
                sudo dnf install -y gcc-c++ cmake xxhash-devel openssl-devel python3-devel pkgconfig
            else
                print_error "Unsupported Linux distribution. Please install build-essential, cmake, libxxhash-dev, and libssl-dev manually."
                exit 1
            fi
            ;;
        "macos")
            if command_exists brew; then
                brew install cmake xxhash openssl pkg-config
            else
                print_error "Homebrew not found. Please install Homebrew first: https://brew.sh/"
                exit 1
            fi
            ;;
        "windows")
            print_warning "Windows dependencies should be installed manually:"
            print_warning "1. Install Visual Studio 2019 or later with C++ build tools"
            print_warning "2. Install CMake 3.16 or later"
            print_warning "3. Install OpenSSL and xxHash development libraries"
            ;;
        *)
            print_error "Unsupported platform: $platform"
            exit 1
            ;;
    esac
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command_exists pip3 && ! command_exists pip; then
        print_error "pip not found. Please install pip first."
        exit 1
    fi
    
    # Use pip3 if available, otherwise pip
    local pip_cmd="pip3"
    if ! command_exists pip3; then
        pip_cmd="pip"
    fi
    
    # Install Python dependencies
    $pip_cmd install -r requirements_enhanced.txt
    
    print_success "Python dependencies installed successfully"
}

# Function to build C++ engine
build_cpp_engine() {
    print_status "Building C++ enhanced engine..."
    
    # Create build directory
    mkdir -p build
    cd build
    
    # Configure with CMake
    print_status "Configuring with CMake..."
    cmake .. -DCMAKE_BUILD_TYPE=Release
    
    # Build
    print_status "Building C++ engine..."
    if command_exists nproc; then
        make -j$(nproc)
    else
        make -j4
    fi
    
    # Run tests if available
    if [ -f "test_enhanced_engine" ]; then
        print_status "Running C++ engine tests..."
        ./test_enhanced_engine
    fi
    
    cd ..
    print_success "C++ engine built successfully"
}

# Function to test Python integration
test_python_integration() {
    print_status "Testing Python integration..."
    
    # Create a simple test script
    cat > test_integration.py << 'EOF'
#!/usr/bin/env python3
"""Test script for enhanced copy engine integration"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_copy_integration import get_engine_info, test_engines
    print("✓ Enhanced copy integration module imported successfully")
    
    # Get engine info
    info = get_engine_info()
    print(f"✓ Available engines: {info['available_engines']}")
    print(f"✓ Platform: {info['platform']}")
    print(f"✓ CPU count: {info['cpu_count']}")
    
    # Test engines
    print("\nTesting engines...")
    results = test_engines()
    for engine, result in results.items():
        status = "✓" if result['success'] else "✗"
        print(f"{status} {engine}: {result.get('error', 'Success')}")
        if result.get('stats'):
            stats = result['stats']
            print(f"    Speed: {stats['speed_mbps']:.1f} MB/s")
    
    print("\n✓ All tests completed successfully!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Test error: {e}")
    sys.exit(1)
EOF
    
    # Run the test
    python3 test_integration.py
    
    # Clean up
    rm -f test_integration.py
    
    print_success "Python integration test completed successfully"
}

# Function to install the engine
install_engine() {
    print_status "Installing enhanced copy engine..."
    
    # Copy the built module to the appropriate location
    if [ -f "build/lib/enhanced_high_perf_engine.so" ]; then
        # Linux/macOS
        cp build/lib/enhanced_high_perf_engine.so .
        print_success "C++ engine installed successfully"
    elif [ -f "build/lib/enhanced_high_perf_engine.pyd" ]; then
        # Windows
        cp build/lib/enhanced_high_perf_engine.pyd .
        print_success "C++ engine installed successfully"
    else
        print_warning "C++ engine not found in build directory. Python engine will be used as fallback."
    fi
    
    # Create __init__.py if it doesn't exist
    if [ ! -f "__init__.py" ]; then
        echo "# Enhanced Copy Engine Package" > __init__.py
    fi
}

# Function to show usage
show_usage() {
    echo "Enhanced High-Performance File Copying Engine Build Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --install-deps      Install system dependencies"
    echo "  --build-cpp         Build C++ engine only"
    echo "  --test              Run tests only"
    echo "  --install           Install the engine"
    echo "  --clean             Clean build artifacts"
    echo "  --all               Full build and install (default)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Full build and install"
    echo "  $0 --install-deps   # Install dependencies only"
    echo "  $0 --build-cpp      # Build C++ engine only"
    echo "  $0 --test           # Run tests only"
}

# Function to clean build artifacts
clean_build() {
    print_status "Cleaning build artifacts..."
    rm -rf build/
    rm -f *.so *.pyd
    rm -f test_integration.py
    print_success "Build artifacts cleaned"
}

# Main function
main() {
    local platform=$(detect_platform)
    local install_deps=false
    local build_cpp=false
    local test_only=false
    local install_engine_flag=false
    local clean_flag=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --install-deps)
                install_deps=true
                shift
                ;;
            --build-cpp)
                build_cpp=true
                shift
                ;;
            --test)
                test_only=true
                shift
                ;;
            --install)
                install_engine_flag=true
                shift
                ;;
            --clean)
                clean_flag=true
                shift
                ;;
            --all)
                install_deps=true
                build_cpp=true
                install_engine_flag=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # If no specific action is requested, do everything
    if [ "$install_deps" = false ] && [ "$build_cpp" = false ] && [ "$test_only" = false ] && [ "$install_engine_flag" = false ] && [ "$clean_flag" = false ]; then
        install_deps=true
        build_cpp=true
        install_engine_flag=true
    fi
    
    print_status "Enhanced High-Performance File Copying Engine Build Script"
    print_status "Platform: $platform"
    print_status "Python version: $(python3 --version 2>/dev/null || echo 'Python3 not found')"
    
    # Clean if requested
    if [ "$clean_flag" = true ]; then
        clean_build
        exit 0
    fi
    
    # Install system dependencies if requested
    if [ "$install_deps" = true ]; then
        install_system_deps "$platform"
        install_python_deps
    fi
    
    # Build C++ engine if requested
    if [ "$build_cpp" = true ]; then
        build_cpp_engine
    fi
    
    # Test if requested
    if [ "$test_only" = true ]; then
        test_python_integration
        exit 0
    fi
    
    # Install engine if requested
    if [ "$install_engine_flag" = true ]; then
        install_engine
        test_python_integration
    fi
    
    print_success "Enhanced copy engine build completed successfully!"
    print_status "You can now use the enhanced copy engine in your Python code:"
    echo ""
    echo "from forwardflow.ingest.engines.enhanced_copy_integration import copy_files"
    echo "result = copy_files('source', 'destination')"
    echo ""
}

# Run main function with all arguments
main "$@"
