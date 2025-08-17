cmake_minimum_required(VERSION 3.16)
project(HighPerfTransferEngine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python and pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# Create the extension module
pybind11_add_module(high_perf_engine high_perf_engine.cpp)

# Set optimization flags for maximum performance
target_compile_options(high_perf_engine PRIVATE
    -O3                    # Maximum optimization
    -march=native         # Use CPU-specific optimizations
    -mtune=native         # Tune for current CPU
    -ffast-math           # Fast math operations
    -funroll-loops        # Unroll loops for better performance
    -flto                 # Link-time optimization
)

# Link against required libraries
target_link_libraries(high_perf_engine PRIVATE
    ${CMAKE_DL_LIBS}     # Dynamic linking
)

# Set output directory
set_target_properties(high_perf_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    PREFIX ""             # No lib prefix
    SUFFIX ".so"          # .so extension on Linux/macOS
)
