#!/bin/bash

# Enhanced High-Performance Copy Engine Build Script
# This script builds the C++ enhanced copy engine with all optimizations

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect platform
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macOS";;
        Linux*)     echo "Linux";;
        CYGWIN*|MINGW32*|MSYS*|MINGW*) echo "Windows";;
        *)          echo "Unknown";;
    esac
}

# Function to install system dependencies
install_system_deps() {
    local platform=$(detect_platform)
    
    print_status "Installing system dependencies for $platform..."
    
    case $platform in
        "macOS")
            if command_exists brew; then
                print_status "Installing dependencies via Homebrew..."
                brew install cmake pkg-config openssl xxhash
            else
                print_warning "Homebrew not found. Please install cmake, pkg-config, openssl, and xxhash manually."
            fi
            ;;
        "Linux")
            if command_exists apt-get; then
                print_status "Installing dependencies via apt-get..."
                sudo apt-get update
                sudo apt-get install -y build-essential cmake pkg-config libssl-dev libxxhash-dev python3-dev python3-pip
            elif command_exists yum; then
                print_status "Installing dependencies via yum..."
                sudo yum groupinstall -y "Development Tools"
                sudo yum install -y cmake pkg-config openssl-devel xxhash-devel python3-devel python3-pip
            elif command_exists dnf; then
                print_status "Installing dependencies via dnf..."
                sudo dnf groupinstall -y "Development Tools"
                sudo dnf install -y cmake pkg-config openssl-devel xxhash-devel python3-devel python3-pip
            else
                print_warning "Package manager not detected. Please install build tools, cmake, pkg-config, openssl, and xxhash manually."
            fi
            ;;
        "Windows")
            print_warning "Windows dependencies should be installed manually:"
            print_warning "- Visual Studio Build Tools"
            print_warning "- CMake"
            print_warning "- OpenSSL"
            print_warning "- xxHash"
            ;;
    esac
    
    print_success "System dependencies installation completed"
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
    $pip_cmd install pybind11 numpy
    
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
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native"
    
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
    
    # Run the test script
    if [ -f "test_enhanced_engine.py" ]; then
        python3 test_enhanced_engine.py
        print_success "Python integration test completed successfully"
    else
        print_warning "Test script not found, skipping Python integration test"
    fi
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
    echo "Enhanced High-Performance Copy Engine Build Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --install-deps      Install system and Python dependencies"
    echo "  --build             Build the C++ engine"
    echo "  --test              Run tests"
    echo "  --install           Install the built engine"
    echo "  --all               Run all steps (default)"
    echo ""
    echo "Examples:"
    echo "  $0 --install-deps   Install dependencies only"
    echo "  $0 --build          Build engine only"
    echo "  $0 --all            Full build process"
}

# Function to run performance benchmark
run_benchmark() {
    print_status "Running performance benchmark..."
    
    if [ -f "test_enhanced_engine.py" ]; then
        # Run benchmark tests
        python3 -c "
import time
from test_enhanced_engine import test_basic_copy, test_large_file

print('Running performance benchmark...')
start_time = time.time()

# Run basic copy test
test_basic_copy()

# Run large file test
test_large_file()

end_time = time.time()
print(f'Benchmark completed in {end_time - start_time:.2f} seconds')
"
        print_success "Performance benchmark completed"
    else
        print_warning "Test script not found, skipping benchmark"
    fi
}

# Main execution
main() {
    local install_deps=false
    local build_engine=false
    local run_tests=false
    local install_engine_flag=false
    local run_all=true
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_usage
                exit 0
                ;;
            --install-deps)
                install_deps=true
                run_all=false
                shift
                ;;
            --build)
                build_engine=true
                run_all=false
                shift
                ;;
            --test)
                run_tests=true
                run_all=false
                shift
                ;;
            --install)
                install_engine_flag=true
                run_all=false
                shift
                ;;
            --all)
                run_all=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Set default behavior
    if $run_all; then
        install_deps=true
        build_engine=true
        run_tests=true
        install_engine_flag=true
    fi
    
    print_status "Enhanced High-Performance Copy Engine Build Process"
    print_status "Platform: $(detect_platform)"
    print_status "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    
    # Install dependencies
    if $install_deps; then
        install_system_deps
        install_python_deps
    fi
    
    # Build engine
    if $build_engine; then
        build_cpp_engine
    fi
    
    # Run tests
    if $run_tests; then
        test_python_integration
        run_benchmark
    fi
    
    # Install engine
    if $install_engine_flag; then
        install_engine
    fi
    
    print_success "Build process completed successfully!"
    print_status "The enhanced copy engine is ready to use."
}

# Run main function with all arguments
main "$@"
