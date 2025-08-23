#pragma once

#include <string>
#include <cstddef>

namespace CrossPlatformIO {

/**
 * Get optimal block size for the platform
 */
size_t get_optimal_block_size();

/**
 * Get optimal thread count for the platform
 */
int get_optimal_thread_count();

/**
 * Open file for direct read access
 */
int open_direct_read(const std::string& path);

/**
 * Open file for direct write access
 */
int open_direct_write(const std::string& path, size_t size = 0);

/**
 * Close file handle
 */
void close_handle(int handle);

/**
 * Read data directly from file
 */
ssize_t read_direct(int handle, void* buffer, size_t size);

/**
 * Write data directly to file
 */
ssize_t write_direct(int handle, const void* buffer, size_t size);

} // namespace CrossPlatformIO
