cmake_minimum_required(VERSION 3.16)
project(EnhancedHighPerfEngine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python and pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# Find OpenSSL for hash functions
find_package(OpenSSL REQUIRED)

# Find xxHash - try multiple methods
find_package(PkgConfig REQUIRED)
pkg_check_modules(XXHASH libxxhash)

# If pkg-config didn't find xxhash, try manual find
if(NOT XXHASH_FOUND)
    find_library(XXHASH_LIBRARY NAMES xxhash libxxhash)
    find_path(XXHASH_INCLUDE_DIR NAMES xxhash.h)
    if(XXHASH_LIBRARY AND XXHASH_INCLUDE_DIR)
        set(XXHASH_FOUND TRUE)
        set(XXHASH_LIBRARIES ${XXHASH_LIBRARY})
        set(XXHASH_INCLUDE_DIRS ${XXHASH_INCLUDE_DIR})
    endif()
endif()

# Manual fallback for Homebrew xxhash on macOS
if(APPLE AND NOT XXHASH_FOUND)
    set(XXHASH_LIBRARY "/opt/homebrew/Cellar/xxhash/0.8.3/lib/libxxhash.a")
    set(XXHASH_INCLUDE_DIR "/opt/homebrew/Cellar/xxhash/0.8.3/include")
    if(EXISTS ${XXHASH_LIBRARY} AND EXISTS ${XXHASH_INCLUDE_DIR})
        set(XXHASH_FOUND TRUE)
        set(XXHASH_LIBRARIES ${XXHASH_LIBRARY})
        set(XXHASH_INCLUDE_DIRS ${XXHASH_INCLUDE_DIR})
        message(STATUS "Found xxHash manually: ${XXHASH_LIBRARY}")
    endif()
endif()

# If still not found, try to find it in standard locations
if(NOT XXHASH_FOUND)
    find_library(XXHASH_LIBRARY NAMES xxhash libxxhash)
    find_path(XXHASH_INCLUDE_DIR NAMES xxhash.h)
    if(XXHASH_LIBRARY AND XXHASH_INCLUDE_DIR)
        set(XXHASH_FOUND TRUE)
        set(XXHASH_LIBRARIES ${XXHASH_LIBRARY})
        set(XXHASH_INCLUDE_DIRS ${XXHASH_INCLUDE_DIR})
    endif()
endif()

# Platform-specific settings
if(WIN32)
    # Windows-specific settings
    add_definitions(-D_WIN32_WINNT=0x0601)  # Windows 7 or later
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /bigobj")
    
    # Windows libraries
    set(PLATFORM_LIBS ws2_32 iphlpapi)
    
elseif(APPLE)
    # macOS-specific settings
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17")
    
    # macOS frameworks
    find_library(COREFOUNDATION_FRAMEWORK CoreFoundation)
    find_library(SYSTEMCONFIGURATION_FRAMEWORK SystemConfiguration)
    set(PLATFORM_LIBS ${COREFOUNDATION_FRAMEWORK} ${SYSTEMCONFIGURATION_FRAMEWORK})
    
else()
    # Linux-specific settings
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17")
    
    # Linux libraries
    set(PLATFORM_LIBS pthread rt)
    
    # Check for posix_fallocate
    include(CheckFunctionExists)
    check_function_exists(posix_fallocate HAVE_POSIX_FALLOCATE)
    if(NOT HAVE_POSIX_FALLOCATE)
        add_definitions(-DNO_POSIX_FALLOCATE)
    endif()
endif()

# Compiler-specific optimizations
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -mtune=native")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -ffast-math -funroll-loops")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
    
    # Enable link-time optimization if available
    include(CheckIPOSupported)
    check_ipo_supported(RESULT ipo_supported)
    if(ipo_supported)
        set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
    endif()
    
elseif(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /O2 /Ob2 /Ot /GL")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /arch:AVX2")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W3")
    
    # Enable link-time optimization
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /GL")
    set(CMAKE_EXE_LINKER_FLAGS_RELEASE "${CMAKE_EXE_LINKER_FLAGS_RELEASE} /LTCG")
endif()

# Create the enhanced high-performance engine
pybind11_add_module(enhanced_high_perf_engine enhanced_high_perf_engine.cpp)

# Link libraries
target_link_libraries(enhanced_high_perf_engine 
    PRIVATE 
    pybind11::module
    OpenSSL::SSL 
    OpenSSL::Crypto
    ${XXHASH_LIBRARIES}
    ${PLATFORM_LIBS}
)

# Include directories
target_include_directories(enhanced_high_perf_engine 
    PRIVATE 
    ${XXHASH_INCLUDE_DIRS}
    ${Python3_INCLUDE_DIRS}
)

# Add library directories
target_link_directories(enhanced_high_perf_engine 
    PRIVATE 
    ${XXHASH_LIBRARY_DIRS}
)

# Compiler definitions
target_compile_definitions(enhanced_high_perf_engine 
    PRIVATE 
    PYTHON_VERSION=${Python3_VERSION}
    $<$<BOOL:${HAVE_POSIX_FALLOCATE}>:HAVE_POSIX_FALLOCATE>
)

# Set output directory
set_target_properties(enhanced_high_perf_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Install target
install(TARGETS enhanced_high_perf_engine
    LIBRARY DESTINATION lib/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages
    RUNTIME DESTINATION bin
)

# Create a simple test executable
add_executable(test_enhanced_engine test_enhanced_engine.cpp)
target_link_libraries(test_enhanced_engine 
    PRIVATE 
    ${PLATFORM_LIBS}
    OpenSSL::SSL 
    OpenSSL::Crypto
    ${XXHASH_LIBRARIES}
)

# Build configuration summary
message(STATUS "Enhanced High-Performance Engine Configuration:")
message(STATUS "  Python version: ${Python3_VERSION}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "  Platform: ${CMAKE_SYSTEM_NAME}")
message(STATUS "  OpenSSL found: ${OpenSSL_FOUND}")
message(STATUS "  xxHash found: ${XXHASH_FOUND}")
if(HAVE_POSIX_FALLOCATE)
    message(STATUS "  posix_fallocate: available")
else()
    message(STATUS "  posix_fallocate: not available")
endif()

# Custom target for building with optimizations
add_custom_target(enhanced_engine_optimized
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target enhanced_high_perf_engine
    COMMENT "Building enhanced high-performance engine with optimizations"
)

# Custom target for running tests
add_custom_target(test_engine
    COMMAND ${CMAKE_BINARY_DIR}/bin/test_enhanced_engine
    DEPENDS test_enhanced_engine
    COMMENT "Running enhanced engine tests"
)

# Documentation target
add_custom_target(docs
    COMMAND ${CMAKE_COMMAND} -E echo "Enhanced High-Performance Engine Documentation:"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Adaptive I/O parameters based on runtime bandwidth detection"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Cross-platform direct I/O with graceful fallback"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Large sequential blocks with tunable parameters"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Multi-threaded copying with range splitting"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Multi-destination copy support"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Cryptographic integrity checks (MD5, SHA-256, xxHash64)"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Network MTU tuning and socket buffer optimization"
    COMMAND ${CMAKE_COMMAND} -E echo "  - Cross-platform abstractions"
    COMMENT "Enhanced engine features documentation"
)
