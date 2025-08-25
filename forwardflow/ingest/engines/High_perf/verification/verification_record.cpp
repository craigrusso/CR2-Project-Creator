#include "verification_record.hpp"
#include <mutex>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <iostream>

namespace Verification {

VerificationRecord::VerificationRecord(const std::string& fname, const std::string& src, 
                                     const std::string& dst, size_t size, const std::string& htype, 
                                     const std::string& src_hash, const std::string& dst_hash, 
                                     const std::string& stat, const std::string& err)
    : filename(fname), source_path(src), destination_path(dst), file_size_bytes(size),
      hash_type(htype), source_hash(src_hash), destination_hash(dst_hash), 
      status(stat), error_message(err) {
    
    // Generate timestamp
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    timestamp = ss.str();
}

std::string HashCalculator::calculate_file_hash(const std::string& file_path, const std::string& algorithm) {
    // For now, return a placeholder - this would integrate with OpenSSL or xxHash
    if (algorithm == "xxhash64") {
        return "xxhash64_placeholder_" + std::to_string(std::filesystem::file_size(file_path));
    } else if (algorithm == "sha256") {
        return "sha256_placeholder_" + std::to_string(std::filesystem::file_size(file_path));
    } else if (algorithm == "md5") {
        return "md5_placeholder_" + std::to_string(std::filesystem::file_size(file_path));
    }
    return "unknown_hash";
}

void VerificationReportManager::add_record(const VerificationRecord& record) {
    std::lock_guard<std::mutex> lock(records_mutex_);
    records_.push_back(record);
}

void VerificationReportManager::write_reports(const std::string& job_id, const std::vector<std::string>& destinations, const std::string& reports_folder_name) {
    for (const auto& dest : destinations) {
        write_verification_reports_to_destination(job_id, dest, reports_folder_name);
    }
}

void VerificationReportManager::write_verification_reports_to_destination(const std::string& job_id, const std::string& dest_path, const std::string& reports_folder_name) {
    try {
        namespace fs = std::filesystem;
        fs::path dest_dir = fs::path(dest_path) / reports_folder_name;
        fs::create_directories(dest_dir);
        
        std::string timestamp = std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count());
        
        fs::path txt_file = dest_dir / (job_id + "_verification_" + timestamp + ".txt");
        fs::path csv_file = dest_dir / (job_id + "_verification_" + timestamp + ".csv");
        
        write_txt_report(txt_file, job_id);
        write_csv_report(csv_file);
        
    } catch (const std::exception& e) {
        std::cerr << "ERROR: Failed to write verification reports: " << e.what() << std::endl;
    }
}

void VerificationReportManager::write_txt_report(const std::filesystem::path& filepath, const std::string& job_id) {
    std::ofstream file(filepath);
    if (!file.is_open()) return;
    
    file << "ForwardFlow Verification Report\n";
    file << "==============================\n";
    file << "Job ID: " << job_id << "\n";
    file << "Generated: " << std::chrono::system_clock::now().time_since_epoch().count() << "\n\n";
    
    std::lock_guard<std::mutex> lock(records_mutex_);
    for (const auto& record : records_) {
        file << "File: " << record.filename << "\n";
        file << "  Source: " << record.source_path << "\n";
        file << "  Destination: " << record.destination_path << "\n";
        file << "  Size: " << format_bytes(record.file_size_bytes) << "\n";
        file << "  Hash: " << record.hash_type << "\n";
        file << "  Status: " << record.status << "\n";
        if (!record.error_message.empty()) {
            file << "  Error: " << record.error_message << "\n";
        }
        file << "\n";
    }
}

void VerificationReportManager::write_csv_report(const std::filesystem::path& filepath) {
    std::ofstream file(filepath);
    if (!file.is_open()) return;
    
    file << "Filename,SourcePath,DestinationPath,SizeBytes,HashType,SourceHash,DestinationHash,Status,Timestamp,ErrorMessage\n";
    
    std::lock_guard<std::mutex> lock(records_mutex_);
    for (const auto& record : records_) {
        file << "\"" << record.filename << "\","
             << "\"" << record.source_path << "\","
             << "\"" << record.destination_path << "\","
             << record.file_size_bytes << ","
             << "\"" << record.hash_type << "\","
             << "\"" << record.source_hash << "\","
             << "\"" << record.destination_hash << "\","
             << "\"" << record.status << "\","
             << "\"" << record.timestamp << "\","
             << "\"" << record.error_message << "\"\n";
    }
}

std::string VerificationReportManager::format_bytes(size_t bytes) {
    const char* units[] = {"B", "KB", "MB", "GB", "TB"};
    int unit_index = 0;
    double size = static_cast<double>(bytes);
    
    while (size >= 1024.0 && unit_index < 4) {
        size /= 1024.0;
        unit_index++;
    }
    
    std::stringstream ss;
    ss << std::fixed << std::setprecision(2) << size << " " << units[unit_index];
    return ss.str();
}

} // namespace Verification
