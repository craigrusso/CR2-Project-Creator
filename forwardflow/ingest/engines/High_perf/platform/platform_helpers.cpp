#include "platform_helpers.hpp"
#include <unistd.h>

namespace PlatformHelpers {

bool is_network_path_macos(const std::string& path) {
#ifdef __APPLE__
    struct statfs s{};
    if (statfs(path.c_str(), &s) != 0) return false; // default local if unknown
    return (s.f_flags & MNT_LOCAL) == 0;
#else
    return false;
#endif
}

bool is_network_path_win(const std::wstring& path) {
#ifdef _WIN32
    // PathIsNetworkPathW is simplest; fallback to GetDriveTypeW check.
    typedef BOOL (WINAPI *PPathIsNetworkPathW)(LPCWSTR);
    static HMODULE h = LoadLibraryW(L"Shlwapi.dll");
    static auto PathIsNetworkPathW = (PPathIsNetworkPathW)(h ? GetProcAddress(h, "PathIsNetworkPathW") : nullptr);
    if (PathIsNetworkPathW) return PathIsNetworkPathW(path.c_str());
    UINT t = GetDriveTypeW(path.substr(0,3).c_str()); // e.g. "Z:\"
    return t == DRIVE_REMOTE;
#else
    return false;
#endif
}

bool is_network_path_linux(const std::string& path) {
#ifdef __linux__
#ifndef CIFS_MAGIC_NUMBER
#define CIFS_MAGIC_NUMBER 0xFF534D42
#endif
#ifndef NFS_SUPER_MAGIC
#define NFS_SUPER_MAGIC 0x6969
#endif

    struct statfs s{};
    if (statfs(path.c_str(), &s) != 0) return false;
    return (s.f_type == (long)CIFS_MAGIC_NUMBER) || (s.f_type == (long)NFS_SUPER_MAGIC);
#else
    return false;
#endif
}

bool is_network_path(const std::string& path) {
#if defined(__APPLE__)
    return is_network_path_macos(path);
#elif defined(_WIN32)
    std::wstring wpath(path.begin(), path.end());
    return is_network_path_win(wpath);
#elif defined(__linux__)
    return is_network_path_linux(path);
#else
    return false;
#endif
}

bool try_clone_only_macos(const std::string& src, const std::string& dst) {
#ifdef __APPLE__
    return clonefile(src.c_str(), dst.c_str(), 0) == 0;
#else
    return false;
#endif
}

bool preallocate_macos(int fd, off_t size) {
#ifdef __APPLE__
    // macOS-specific preallocation using fcntl
    // Note: This is a simplified version - in practice you'd need proper macOS headers
    return ftruncate(fd, size) == 0;
#else
    return false;
#endif
}

bool preallocate_linux(int fd, off_t size) {
#ifdef __linux__
    if (posix_fallocate(fd, 0, size) == 0) return (ftruncate(fd, size) == 0 || errno == 0);
    return ftruncate(fd, size) == 0;
#else
    return false;
#endif
}

#ifdef _WIN32
bool preallocate_windows(HANDLE h, LONGLONG size) {
    LARGE_INTEGER li; li.QuadPart = size;
    if (!SetFilePointerEx(h, li, nullptr, FILE_BEGIN)) return false;
    return SetEndOfFile(h);
}
#endif

bool try_fast_copy_macos(const std::string& src, const std::string& dst) {
#ifdef __APPLE__
    // APFS clone first (same volume)
    if (clonefile(src.c_str(), dst.c_str(), 0) == 0) return true;
    copyfile_state_t st = copyfile_state_alloc();
    int rc = copyfile(src.c_str(), dst.c_str(), st, COPYFILE_DATA);
    copyfile_state_free(st);
    return rc == 0;
#else
    return false;
#endif
}

} // namespace PlatformHelpers
