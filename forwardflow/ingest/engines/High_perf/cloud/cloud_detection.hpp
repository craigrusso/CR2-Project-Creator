#pragma once

#include <string>
#include <vector>

namespace CloudDetection {

/**
 * Detects if a path is on cloud storage (macOS)
 * Covers OneDrive, iCloud Drive, Google Drive, Dropbox, and other cloud providers
 */
bool is_cloud_storage_path_macos(const std::string& path);

/**
 * Detects if a path is on cloud storage (cross-platform)
 */
bool is_cloud_storage_path(const std::string& path);

} // namespace CloudDetection
