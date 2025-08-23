#pragma once

#include <string>

// Platform-specific includes
#ifdef _WIN32
    #include <windows.h>
    #include <winioctl.h>
    #include <io.h>
    #include <direct.h>
    #include <shlwapi.h>
#elif defined(__APPLE__)
    #include <copyfile.h>
    #include <sys/param.h>
    #include <sys/mount.h>
    #include <sys/socket.h>
    #include <net/if.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <sys/ioctl.h>
    #include <sys/clonefile.h>
    #include <sys/mount.h>  // statfs is in mount.h on macOS
#else
    #include <sys/sendfile.h>
    #include <linux/fs.h>
    #include <linux/fiemap.h>
    #include <sys/socket.h>
    #include <net/if.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <sys/ioctl.h>
    #include <linux/sockios.h>
    #include <sys/vfs.h>
#endif

namespace PlatformHelpers {

/**
 * Detect if a path is on network storage (macOS)
 */
bool is_network_path_macos(const std::string& path);

/**
 * Detect if a path is on network storage (Windows)
 */
bool is_network_path_win(const std::wstring& path);

/**
 * Detect if a path is on network storage (Linux)
 */
bool is_network_path_linux(const std::string& path);

/**
 * Detect if a path is on network storage (cross-platform)
 */
bool is_network_path(const std::string& path);

/**
 * Try clone-only copy on macOS (APFS)
 */
bool try_clone_only_macos(const std::string& src, const std::string& dst);

/**
 * Preallocate file on macOS
 */
bool preallocate_macos(int fd, off_t size);

/**
 * Preallocate file on Linux
 */
bool preallocate_linux(int fd, off_t size);

    /**
     * Preallocate file on Windows
     */
#ifdef _WIN32
    bool preallocate_windows(HANDLE h, LONGLONG size);
#endif

/**
 * Try fast copy on macOS
 */
bool try_fast_copy_macos(const std::string& src, const std::string& dst);

} // namespace PlatformHelpers
