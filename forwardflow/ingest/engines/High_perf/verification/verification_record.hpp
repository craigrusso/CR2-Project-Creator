#pragma once

#include <string>
#include <vector>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <filesystem>

namespace Verification {

/**
 * Structure for verification records
 */
struct VerificationRecord {
    std::string filename;
    std::string source_path;
    std::string destination_path;
    size_t file_size_bytes;
    std::string hash_type;
    std::string source_hash;
    std::string destination_hash;
    std::string status;  // "PASS" or "FAIL"
    std::string timestamp;
    std::string error_message;
    
    VerificationRecord() = default;
    VerificationRecord(const std::string& fname, const std::string& src, const std::string& dst, 
                      size_t size, const std::string& htype, const std::string& src_hash, 
                      const std::string& dst_hash, const std::string& stat, const std::string& err = "");
};

/**
 * Hash calculation utilities
 */
class HashCalculator {
public:
    static std::string calculate_file_hash(const std::string& file_path, const std::string& algorithm = "xxhash64");
};

/**
 * Verification report manager
 */
class VerificationReportManager {
public:
    void add_record(const VerificationRecord& record);
    void write_reports(const std::string& job_id, const std::vector<std::string>& destinations, const std::string& reports_folder_name = "_ForwardFlow_Reports");
    void write_verification_reports_to_destination(const std::string& job_id, const std::string& dest_path, const std::string& reports_folder_name = "_ForwardFlow_Reports");
    
private:
    std::vector<VerificationRecord> records_;
    std::mutex records_mutex_;
    
    void write_txt_report(const std::filesystem::path& filepath, const std::string& job_id);
    void write_csv_report(const std::filesystem::path& filepath);
    std::string format_bytes(size_t bytes);
};

} // namespace Verification
