#include "cross_platform_io.hpp"
#include <thread>
#include <fcntl.h>
#include <unistd.h>

// Platform-specific includes
#ifdef _WIN32
    #include <windows.h>
    #include <io.h>
#elif defined(__APPLE__)
    #include <fcntl.h>
    #include <unistd.h>
    #include "../cloud/cloud_detection.hpp"
#else
    #include <fcntl.h>
    #include <unistd.h>
#endif

namespace CrossPlatformIO {

size_t get_optimal_block_size() {
#ifdef _WIN32
    return 64 * 1024;  // 64KB for Windows
#else
    return 1024 * 1024;  // 1MB for Unix-like systems
#endif
}

int get_optimal_thread_count() {
    int cores = std::thread::hardware_concurrency();
    return std::min(32, cores * 2);
}

int open_direct_read(const std::string& path) {
    try {
#ifdef _WIN32
        HANDLE handle = CreateFileA(
            path.c_str(),
            GENERIC_READ,
            FILE_SHARE_READ,
            nullptr,
            OPEN_EXISTING,
            FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN,
            nullptr
        );
        return reinterpret_cast<int>(handle);
#elif defined(__APPLE__)
        int fd = open(path.c_str(), O_RDONLY);
        if (fd != -1) {
            // Skip F_NOCACHE for cloud storage to avoid hanging
            if (!CloudDetection::is_cloud_storage_path_macos(path)) {
                fcntl(fd, F_NOCACHE, 1);
            }
        }
        return fd;
#else
        return open(path.c_str(), O_RDONLY | O_DIRECT);
#endif
    } catch (...) {
        return -1;
    }
}

int open_direct_write(const std::string& path, size_t size) {
    try {
#ifdef _WIN32
        HANDLE handle = CreateFileA(
            path.c_str(),
            GENERIC_WRITE,
            0,
            nullptr,
            CREATE_ALWAYS,
            FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN,
            nullptr
        );
        if (handle != INVALID_HANDLE_VALUE && size > 0) {
            LARGE_INTEGER li;
            li.QuadPart = size;
            SetFilePointerEx(handle, li, nullptr, FILE_BEGIN);
            SetEndOfFile(handle);
        }
        return reinterpret_cast<int>(handle);
#elif defined(__APPLE__)
        int fd = open(path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd != -1) {
            fcntl(fd, F_NOCACHE, 1);
            if (size > 0) {
                ftruncate(fd, size);
            }
        }
        return fd;
#else
        int fd = open(path.c_str(), O_WRONLY | O_CREAT | O_TRUNC | O_DIRECT, 0644);
        if (fd != -1 && size > 0) {
            // Use fallocate if available
#ifdef _GNU_SOURCE
            fallocate(fd, 0, 0, size);
#endif
        }
        return fd;
#endif
    } catch (...) {
        return -1;
    }
}

void close_handle(int handle) {
    try {
#ifdef _WIN32
        CloseHandle(reinterpret_cast<HANDLE>(handle));
#else
        close(handle);
#endif
    } catch (...) {}
}

ssize_t read_direct(int handle, void* buffer, size_t size) {
    try {
#ifdef _WIN32
        DWORD bytes_read;
        BOOL result = ReadFile(
            reinterpret_cast<HANDLE>(handle),
            buffer,
            static_cast<DWORD>(size),
            &bytes_read,
            nullptr
        );
        return result ? bytes_read : -1;
#else
        return read(handle, buffer, size);
#endif
    } catch (...) {
        return -1;
    }
}

ssize_t write_direct(int handle, const void* buffer, size_t size) {
    try {
#ifdef _WIN32
        DWORD bytes_written;
        BOOL result = WriteFile(
            reinterpret_cast<HANDLE>(handle),
            buffer,
            static_cast<DWORD>(size),
            &bytes_written,
            nullptr
        );
        return result ? bytes_written : -1;
#else
        return write(handle, buffer, size);
#endif
    } catch (...) {
        return -1;
    }
}

} // namespace CrossPlatformIO
