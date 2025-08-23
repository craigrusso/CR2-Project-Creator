cmake_minimum_required(VERSION 3.16)
project(ForwardFlowHighPerfEngine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Force CMake to use the system Python framework that pybind11 is actually using
set(PYTHON_EXECUTABLE "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3")
set(PYTHON_INCLUDE_DIR "/Library/Frameworks/Python.framework/Versions/3.12/include/python3.12")
set(PYTHON_LIBRARY "/Library/Frameworks/Python.framework/Versions/3.12/Python")

# Force PyBind11 to use the same installation as Python
set(PYBIND11_PYTHON_VERSION 3.12)
set(PYBIND11_INCLUDE_DIR "/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/pybind11/include")

# Find required packages with forced Python paths
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${PYTHON_INCLUDE_DIR})
include_directories(${PYBIND11_INCLUDE_DIR})

# Use the enhanced engine source file
set(MAIN_SOURCES
    enhanced_engine_main.cpp
)

# Create the Python module - pybind11 will handle Python linking automatically
pybind11_add_module(enhanced_high_perf_engine ${MAIN_SOURCES})

# Explicitly link against the correct Python framework
target_link_libraries(enhanced_high_perf_engine PRIVATE ${PYTHON_LIBRARY})

# Set compiler flags with C++17 requirement
target_compile_options(enhanced_high_perf_engine PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wall -Wextra -O3 -march=native -std=c++17>
    $<$<CXX_COMPILER_ID:Clang>:-Wall -Wextra -O3 -march=native -std=c++17>
    $<$<CXX_COMPILER_ID:AppleClang>:-Wall -Wextra -O3 -std=c++17>
    $<$<CXX_COMPILER_ID:MSVC>:/W3 /O2 /std:c++17>
)

# Platform-specific settings
if(APPLE)
    target_compile_options(enhanced_high_perf_engine PRIVATE
        -D__APPLE__
    )
elseif(WIN32)
    target_compile_options(enhanced_high_perf_engine PRIVATE
        -D_WIN32
        -D_WIN32_WINNT=0x0601
    )
elseif(UNIX AND NOT APPLE)
    target_compile_options(enhanced_high_perf_engine PRIVATE
        -D__linux__
    )
endif()

# Set output directory
set_target_properties(enhanced_high_perf_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

# Install target
install(TARGETS enhanced_high_perf_engine
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/..
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/..
)
