#include "cloud_materialization.hpp"
#include <filesystem>
#include <random>
#include <stdexcept>
#include <iostream>
#include <cerrno>
#include <cstring>

#ifdef __APPLE__
#include <copyfile.h>
#endif

namespace CloudMaterialization {

std::string materialize_to_local_temp(const std::string& src, const std::string& job_id) {
#ifdef __APPLE__
    try {
        namespace fs = std::filesystem;
        
        // Create staging directory
        fs::path staging_dir = fs::temp_directory_path() / "ForwardFlowStaging" / job_id;
        fs::create_directories(staging_dir);
        
        // Generate unique temp filename
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(100000, 999999);
        std::string temp_name = "cloud_" + std::to_string(dis(gen)) + "_" + fs::path(src).filename().string();
        fs::path temp_path = staging_dir / temp_name;
        
        // Get source file size for verification
        size_t source_size = fs::file_size(src);
        
        // Use copyfile to force hydration (macOS native)
        if (copyfile(src.c_str(), temp_path.c_str(), nullptr, COPYFILE_DATA) != 0) {
            throw std::runtime_error("Failed to hydrate cloud file: " + std::string(strerror(errno)));
        }
        
        // Verify size matches
        size_t temp_size = fs::file_size(temp_path);
        if (temp_size != source_size) {
            fs::remove(temp_path);
            throw std::runtime_error("Hydrated file size mismatch: expected " + std::to_string(source_size) + 
                                   ", got " + std::to_string(temp_size));
        }
        
        return temp_path.string();
        
    } catch (const std::exception& e) {
        std::cerr << "ERROR: Failed to materialize cloud file: " << e.what() << std::endl;
        throw;
    }
#else
    // For non-macOS platforms, return the original path
    // This could be extended with platform-specific implementations
    return src;
#endif
}

void cleanup_temp_file(const std::string& temp_path) {
    try {
        if (!temp_path.empty() && temp_path != "/") {
            std::filesystem::remove(temp_path);
        }
    } catch (const std::exception& e) {
        std::cerr << "WARNING: Failed to cleanup temp file: " << e.what() << std::endl;
    }
}

} // namespace CloudMaterialization
