#pragma once

#include <string>

namespace CloudMaterialization {

/**
 * Materializes a cloud file to a local temporary location for reliable copying
 * Uses copyfile with COPYFILE_DATA to force hydration on macOS
 */
std::string materialize_to_local_temp(const std::string& src, const std::string& job_id);

/**
 * Cleans up temporary materialized files
 */
void cleanup_temp_file(const std::string& temp_path);

} // namespace CloudMaterialization
