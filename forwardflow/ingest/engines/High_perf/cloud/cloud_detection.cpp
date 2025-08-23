#include "cloud_detection.hpp"
#include <algorithm>
#include <cctype>

namespace CloudDetection {

bool is_cloud_storage_path_macos(const std::string& path) {
    std::string lower_path = path;
    std::transform(lower_path.begin(), lower_path.end(), lower_path.begin(), ::tolower);
    
    // Check for cloud storage patterns
    const std::vector<std::string> cloud_patterns = {
        "/library/cloudstorage/",
        "/onedrive",
        "/icloud drive",
        "/google drive",
        "/dropbox",
        "/box",
        "/mega",
        "/pcloud",
        "/sync.com",
        "/tresorit"
    };
    
    for (const auto& pattern : cloud_patterns) {
        if (lower_path.find(pattern) != std::string::npos) {
            return true;
        }
    }
    
    return false;
}

bool is_cloud_storage_path(const std::string& path) {
#ifdef __APPLE__
    return is_cloud_storage_path_macos(path);
#else
    // For other platforms, implement similar detection logic
    std::string lower_path = path;
    std::transform(lower_path.begin(), lower_path.end(), lower_path.begin(), ::tolower);
    
    // Windows cloud patterns
    if (lower_path.find("onedrive") != std::string::npos) return true;
    if (lower_path.find("icloud drive") != std::string::npos) return true;
    if (lower_path.find("google drive") != std::string::npos) return true;
    if (lower_path.find("dropbox") != std::string::npos) return true;
    
    // Linux cloud patterns
    if (lower_path.find("/mnt/onedrive") != std::string::npos) return true;
    if (lower_path.find("/mnt/icloud") != std::string::npos) return true;
    if (lower_path.find("/mnt/google-drive") != std::string::npos) return true;
    
    return false;
#endif
}

} // namespace CloudDetection
