#include "engine_core.hpp"
#include <chrono>
#include <iostream>
#include <sstream> // Required for std::stringstream
#include <iomanip> // Required for std::put_time
#include <fstream> // Required for std::ofstream
#include "../verification/verification_record.hpp" // For verification records

namespace EngineCore {

EnhancedHighPerfTransferEngine::EnhancedHighPerfTransferEngine() = default;

void EnhancedHighPerfTransferEngine::set_event_sink(std::function<void(const std::string&, const void*)> sink) {
    event_sink_ = sink;
}

DataStructures::CopyStats EnhancedHighPerfTransferEngine::copy_files(const DataStructures::CopyJob& job) {
    // Initialize stats
    stats_ = DataStructures::CopyStats{};
    stats_.start_time = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count() / 1000.0;
    
    try {
        // Debug: Print job information
        std::cout << "DEBUG: C++ engine copy_files called" << std::endl;
        std::cout << "DEBUG: Source paths count: " << job.source_paths.size() << std::endl;
        for (const auto& path : job.source_paths) {
            std::cout << "DEBUG: Source path: " << path << std::endl;
        }
        std::cout << "DEBUG: Destination paths count: " << job.destination_paths.size() << std::endl;
        for (const auto& path : job.destination_paths) {
            std::cout << "DEBUG: Destination path: " << path << std::endl;
        }
        
        // Reset stats for new job
        stats_ = DataStructures::CopyStats{};
        stats_.start_time = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count() / 1000.0;
        
        // Collect all files to copy first to get accurate stats
        auto files = collect_files(job.source_paths);
        std::cout << "DEBUG: Collected " << files.size() << " files to copy" << std::endl;
        
        stats_.total_files = files.size();
        
        // Calculate total bytes
        for (const auto& file : files) {
            try {
                size_t file_size = std::filesystem::file_size(file);
                stats_.total_bytes += file_size;
                std::cout << "DEBUG: File: " << file << " size: " << file_size << " bytes" << std::endl;
            } catch (const std::exception& e) {
                std::cout << "DEBUG: Failed to get size for " << file << ": " << e.what() << std::endl;
                add_error("Failed to get size for " + file + ": " + e.what());
            }
        }
        
        std::cout << "DEBUG: Total bytes to copy: " << stats_.total_bytes << std::endl;
        
        // Check disk space for each destination before starting
        for (const auto& dest : job.destination_paths) {
            if (!check_disk_space(dest, stats_.total_bytes)) {
                std::string error_msg = "Insufficient disk space on destination: " + dest;
                std::cout << "ERROR: " << error_msg << std::endl;
                add_error(error_msg);
                
                // Emit job error event
                emit_event("job.error", nullptr);
                return stats_;  // Fail fast - don't start copying
            }
        }
        
        // Emit job started event with proper payload
        struct JobStartedPayload {
            const char* job_id;
            size_t total_bytes;
            size_t total_files;
        };
        JobStartedPayload job_started_payload = {"", stats_.total_bytes, static_cast<size_t>(stats_.total_files)};
        emit_event("job.started", &job_started_payload);
        
        // Emit job progress event with initial progress data
        struct JobProgressPayload {
            const char* job_id;
            size_t bytes_copied;
            size_t total_bytes;
            size_t files_completed;
            size_t total_files;
            double elapsed;
            double speed_mbps;
        };
        JobProgressPayload initial_progress = {
            "",  // job_id
            0,   // bytes_copied (start at 0)
            stats_.total_bytes,
            0,   // files_completed (start at 0)
            static_cast<size_t>(stats_.total_files),
            0.0, // elapsed (start at 0)
            0.0  // speed_mbps (start at 0)
        };
        emit_event("job.progress", &initial_progress);
        
        // Determine copy strategy based on destination count
        if (job.destination_paths.size() == 1) {
            std::cout << "DEBUG: Using single destination copy strategy" << std::endl;
            copy_to_single_destination(job, files);
        } else {
            std::cout << "DEBUG: Using multiple destination copy strategy" << std::endl;
            copy_to_multiple_destinations(job, files);
        }
        
        std::cout << "DEBUG: Copy operation completed. Copied bytes: " << stats_.copied_bytes << std::endl;
        std::cout << "DEBUG: Copied files: " << stats_.copied_files << std::endl;
        
        // Emit job completed event with proper payload
        struct JobCompletedPayload {
            const char* job_id;
            size_t bytes_copied;
            size_t total_bytes;
            double elapsed;
            double speed_mbps;
        };
        JobCompletedPayload job_completed_payload = {"", stats_.copied_bytes, stats_.total_bytes, stats_.duration(), stats_.speed_mbps};
        emit_event("job.completed", &job_completed_payload);
        
        // Generate verification reports if requested - async to avoid blocking
        if (job.generate_verification_report) {
            std::cout << "DEBUG: Scheduling async verification reports..." << std::endl;
            // Note: Verification report writing will be handled by Python layer asynchronously
            // This avoids blocking the main thread and UI during report generation
            std::cout << "DEBUG: Verification reports will be written asynchronously by Python layer" << std::endl;
        }
        
    } catch (const std::exception& e) {
        std::cout << "DEBUG: Exception in copy_files: " << e.what() << std::endl;
        add_error("Copy operation failed: " + std::string(e.what()));
        
        // Emit job error event
        emit_event("job.error", nullptr);
    }
    
    // Finalize stats
    stats_.end_time = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count() / 1000.0;
    
    if (stats_.duration() > 0) {
        stats_.speed_mbps = (stats_.copied_bytes / (1024.0 * 1024.0)) / stats_.duration();
    }
    
    return stats_;
}

// Disk space validation methods
size_t EnhancedHighPerfTransferEngine::get_available_disk_space(const std::string& path) {
    try {
        std::filesystem::space_info space = std::filesystem::space(path);
        return space.available;
    } catch (const std::exception& e) {
        std::cout << "ERROR: Failed to get disk space for " << path << ": " << e.what() << std::endl;
        return 0;
    }
}

bool EnhancedHighPerfTransferEngine::check_disk_space(const std::string& destination_path, size_t required_bytes) {
    size_t available = get_available_disk_space(destination_path);
    
    if (available < required_bytes) {
        std::cout << "ERROR: Insufficient disk space on " << destination_path << std::endl;
        std::cout << "ERROR: Required: " << required_bytes << " bytes, Available: " << available << " bytes" << std::endl;
        std::cout << "ERROR: Need " << (required_bytes - available) << " more bytes" << std::endl;
        return false;
    }
    
    std::cout << "DEBUG: Disk space check passed - Available: " << available << " bytes, Required: " << required_bytes << " bytes" << std::endl;
    return true;
}

void EnhancedHighPerfTransferEngine::cancel() {
    cancelled_.store(true);
}

void EnhancedHighPerfTransferEngine::pause() {
    paused_.store(true);
}

void EnhancedHighPerfTransferEngine::resume() {
    paused_.store(false);
}

void EnhancedHighPerfTransferEngine::write_verification_reports(const DataStructures::CopyJob& job) {
    // Implementation would write verification reports
    if (job.generate_verification_report) {
        // Use verification manager to write reports
    }
}

void EnhancedHighPerfTransferEngine::write_verification_reports_to_destination(const DataStructures::CopyJob& job, const std::string& dest_path) {
    // Implementation would write verification reports to specific destination
    if (job.generate_verification_report) {
        try {
            std::cout << "DEBUG: Writing verification reports to destination: " << dest_path << std::endl;
            
            // Create verification report directory
            std::filesystem::path dest_dir(dest_path);
            std::filesystem::path report_dir = dest_dir / "ForwardFlow_Verification_Reports";
            std::filesystem::create_directories(report_dir);
            
            // Generate timestamp
            auto now = std::chrono::system_clock::now();
            auto time_t = std::chrono::system_clock::to_time_t(now);
            std::stringstream timestamp_ss;
            timestamp_ss << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S");
            std::string timestamp = timestamp_ss.str();
            
            // Write verification report files
            std::filesystem::path txt_file = report_dir / (job.job_id + "_verification_" + timestamp + ".txt");
            std::filesystem::path csv_file = report_dir / (job.job_id + "_verification_" + timestamp + ".csv");
            
            // Write text report with individual file details
            std::ofstream txt_report(txt_file);
            if (txt_report.is_open()) {
                txt_report << "ForwardFlow Verification Report\n";
                txt_report << "=============================\n\n";
                txt_report << "Job ID: " << job.job_id << "\n";
                txt_report << "Timestamp: " << timestamp << "\n";
                txt_report << "Source: " << (job.source_paths.empty() ? "N/A" : job.source_paths[0]) << "\n";
                txt_report << "Destination: " << dest_path << "\n";
                txt_report << "Total Files: " << stats_.copied_files << "\n";
                txt_report << "Total Bytes: " << stats_.copied_bytes << "\n";
                txt_report << "Duration: " << std::fixed << std::setprecision(2) << stats_.duration() << " seconds\n";
                txt_report << "Average Speed: " << std::fixed << std::setprecision(2) << stats_.speed_mbps << " MB/s\n\n";
                
                txt_report << "Individual File Verification Results:\n";
                txt_report << "===================================\n";
                
                // Write individual file records
                std::lock_guard<std::mutex> lock(verification_mu_);
                for (const auto& record : verification_records_) {
                    txt_report << "\nFile: " << record.filename << "\n";
                    txt_report << "  Source: " << record.source_path << "\n";
                    txt_report << "  Destination: " << record.destination_path << "\n";
                    txt_report << "  Size: " << record.file_size_bytes << " bytes\n";
                    txt_report << "  Hash Type: " << record.hash_type << "\n";
                    txt_report << "  Source Hash: " << record.source_hash << "\n";
                    txt_report << "  Destination Hash: " << record.destination_hash << "\n";
                    txt_report << "  Status: " << record.status << "\n";
                    txt_report << "  Timestamp: " << record.timestamp << "\n";
                    if (!record.error_message.empty()) {
                        txt_report << "  Error: " << record.error_message << "\n";
                    }
                }
                
                txt_report.close();
                std::cout << "DEBUG: Text verification report written to: " << txt_file << std::endl;
            }
            
            // Write CSV report with individual file details
            std::ofstream csv_report(csv_file);
            if (csv_report.is_open()) {
                csv_report << "Filename,SourcePath,DestinationPath,SizeBytes,HashType,SourceHash,DestinationHash,Status,Timestamp,ErrorMessage\n";
                
                // Write individual file records
                std::lock_guard<std::mutex> lock(verification_mu_);
                for (const auto& record : verification_records_) {
                    csv_report << "\"" << record.filename << "\","
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
                
                csv_report.close();
                std::cout << "DEBUG: CSV verification report written to: " << csv_file << std::endl;
            }
            
            std::cout << "DEBUG: Verification reports successfully written to: " << report_dir << std::endl;
            
        } catch (const std::exception& e) {
            std::cout << "DEBUG: Error writing verification reports: " << e.what() << std::endl;
            throw; // Re-throw to let caller handle
        }
    }
}

// Helper methods
void EnhancedHighPerfTransferEngine::add_bytes(size_t n) {
    std::lock_guard<std::mutex> lock(stats_mu_);
    stats_.copied_bytes += n;
}

void EnhancedHighPerfTransferEngine::inc_files() {
    std::lock_guard<std::mutex> lock(stats_mu_);
    stats_.copied_files++;
}

void EnhancedHighPerfTransferEngine::add_error(const std::string& e) {
    std::lock_guard<std::mutex> lock(stats_mu_);
    stats_.errors.push_back(e);
}

void EnhancedHighPerfTransferEngine::add_verification_record(const Verification::VerificationRecord& record) {
    std::lock_guard<std::mutex> lock(verification_mu_);
    verification_records_.push_back(record);
}

// File operations
std::vector<std::string> EnhancedHighPerfTransferEngine::collect_files(const std::vector<std::string>& source_paths) {
    std::vector<std::string> files;
    
    std::cout << "DEBUG: collect_files called with " << source_paths.size() << " source paths" << std::endl;
    
    for (const auto& source_path : source_paths) {
        std::cout << "DEBUG: Processing source path: " << source_path << std::endl;
        try {
            if (std::filesystem::is_directory(source_path)) {
                std::cout << "DEBUG: Source path is a directory, scanning recursively..." << std::endl;
                // Recursively scan directory
                for (const auto& entry : std::filesystem::recursive_directory_iterator(source_path)) {
                    if (std::filesystem::is_regular_file(entry)) {
                        std::string file_path = entry.path().string();
                        files.push_back(file_path);
                        std::cout << "DEBUG: Found file: " << file_path << std::endl;
                    }
                }
                std::cout << "DEBUG: Found " << files.size() << " files in directory" << std::endl;
            } else if (std::filesystem::is_regular_file(source_path)) {
                std::cout << "DEBUG: Source path is a regular file" << std::endl;
                // Single file
                files.push_back(source_path);
            } else {
                std::cout << "DEBUG: Source path is neither directory nor regular file" << std::endl;
            }
        } catch (const std::exception& e) {
            std::cout << "DEBUG: Exception scanning source path " << source_path << ": " << e.what() << std::endl;
            add_error("Failed to scan source path " + source_path + ": " + e.what());
        }
    }
    
    std::cout << "DEBUG: collect_files returning " << files.size() << " files" << std::endl;
    return files;
}

void EnhancedHighPerfTransferEngine::copy_to_single_destination(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    for (const auto& file : files) {
        if (cancelled_.load()) {
            std::cout << "DEBUG: Job cancelled, emitting cancellation event" << std::endl;
            emit_event("job.cancelled", nullptr);
            break;
        }
        
        // Get file info for events
        std::string filename = std::filesystem::path(file).filename().string();
        std::string file_id = "file_" + std::to_string(files_processed_);
        size_t file_size = std::filesystem::file_size(file);
        
        // Emit file started event with file context
        struct FileStartedPayload {
            const char* file_id;
            const char* filename;
            size_t total_bytes;
        };
        FileStartedPayload file_started_payload = {file_id.c_str(), filename.c_str(), file_size};
        emit_event("file.started", &file_started_payload);
        
        for (const auto& dest : job.destination_paths) {
            if (copy_single_file(job, file, dest)) {
                inc_files();
                
                // Emit file completed event with file context
                struct FileCompletedPayload {
                    const char* file_id;
                    const char* filename;
                    size_t bytes_copied;
                    size_t total_bytes;
                    bool skipped;
                };
                FileCompletedPayload file_completed_payload = {file_id.c_str(), filename.c_str(), file_size, file_size, false};
                emit_event("file.completed", &file_completed_payload);
            }
        }
        
        files_processed_++;
        
        // Emit job progress update after each file completion
        struct JobProgressPayload {
            const char* job_id;
            size_t bytes_copied;
            size_t total_bytes;
            size_t files_completed;
            size_t total_files;
            double elapsed;
            double speed_mbps;
        };
        
        // Calculate current progress
        double elapsed_seconds = stats_.duration();
        double current_speed_mbps = 0.0;
        if (elapsed_seconds > 0) {
            current_speed_mbps = (stats_.copied_bytes / (1024.0 * 1024.0)) / elapsed_seconds;
        }
        
        JobProgressPayload progress_payload = {
            "",  // job_id (will be filled by Python side)
            stats_.copied_bytes,
            0,   // total_bytes (will be filled by Python side) 
            files_processed_,  // files completed
            static_cast<size_t>(files.size()),  // total files
            elapsed_seconds,
            current_speed_mbps
        };
        emit_event("job.progress", &progress_payload);
    }
}

void EnhancedHighPerfTransferEngine::copy_to_multiple_destinations(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    // Use fan-out strategy for multiple destinations
    copy_to_multiple_destinations_fanout(job, files);
}

void EnhancedHighPerfTransferEngine::copy_to_multiple_destinations_fanout(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    for (const auto& file : files) {
        if (cancelled_.load()) {
            std::cout << "DEBUG: Job cancelled, emitting cancellation event" << std::endl;
            emit_event("job.cancelled", nullptr);
            break;
        }
        
        // Get file info for events
        std::string filename = std::filesystem::path(file).filename().string();
        std::string file_id = "file_" + std::to_string(files_processed_);
        size_t file_size = std::filesystem::file_size(file);
        
        // Emit file started event with file context
        struct FileStartedPayload {
            const char* file_id;
            const char* filename;
            size_t total_bytes;
        };
        FileStartedPayload file_started_payload = {file_id.c_str(), filename.c_str(), file_size};
        emit_event("file.started", &file_started_payload);
        
        // Use the copy_file_to_many function for efficient fan-out
        std::vector<DataStructures::TunedParams> tuned_params;
        if (job.per_dest_params.empty()) {
            // Create default tuned params for each destination
            for (size_t i = 0; i < job.destination_paths.size(); ++i) {
                tuned_params.push_back(DataStructures::TunedParams{});
            }
        } else {
            tuned_params = job.per_dest_params;
        }
        
        // Copy to each destination with real-time progress updates
        for (const auto& dest : job.destination_paths) {
            if (copy_single_file(job, file, dest)) {
                inc_files();
                
                // Emit file completed event with file context
                struct FileCompletedPayload {
                    const char* file_id;
                    const char* filename;
                    size_t bytes_copied;
                    size_t total_bytes;
                    bool skipped;
                };
                FileCompletedPayload file_completed_payload = {file_id.c_str(), filename.c_str(), file_size, file_size, false};
                emit_event("file.completed", &file_completed_payload);
            }
        }
        
        files_processed_++;
    }
}

bool EnhancedHighPerfTransferEngine::copy_single_file(const DataStructures::CopyJob& job, const std::string& source_path, const std::string& dest_path) {
    std::cout << "DEBUG: copy_single_file called with source: " << source_path << " dest: " << dest_path << std::endl;
    
    try {
        // dest_path is actually the destination directory, not a full file path
        // We need to combine it with the source filename to create the full destination file path
        std::filesystem::path dest_dir = dest_path;
        std::cout << "DEBUG: Destination directory: " << dest_dir.string() << std::endl;
        
        // Create destination directory if it doesn't exist
        if (!std::filesystem::exists(dest_dir)) {
            std::cout << "DEBUG: Creating destination directory..." << std::endl;
            std::filesystem::create_directories(dest_dir);
        }
        
        // Get file info for progress updates
        std::string filename = std::filesystem::path(source_path).filename().string();
        size_t file_size = std::filesystem::file_size(source_path);
        std::string file_id = "file_" + std::to_string(files_processed_);
        
        // Create destination path by combining dest_dir with source filename
        std::filesystem::path source_file = std::filesystem::path(source_path).filename();
        std::filesystem::path final_dest_path = dest_dir / source_file;
        std::cout << "DEBUG: Final destination path: " << final_dest_path.string() << std::endl;
        
        // Open source file for reading
        std::ifstream source_file_stream(source_path, std::ios::binary);
        if (!source_file_stream.is_open()) {
            std::cout << "DEBUG: Failed to open source file: " << source_path << std::endl;
            add_error("Failed to open source file: " + source_path);
            return false;
        }
        
        // Open destination file for writing
        std::ofstream dest_file_stream(final_dest_path, std::ios::binary);
        if (!dest_file_stream.is_open()) {
            std::cout << "DEBUG: Failed to open destination file: " << final_dest_path.string() << std::endl;
            add_error("Failed to open destination file: " + final_dest_path.string());
            return false;
        }
        
        // Copy file with progress updates
        const size_t buffer_size = 1024 * 1024;  // 1MB buffer for high performance
        std::vector<char> buffer(buffer_size);
        size_t total_copied = 0;
        size_t last_progress_update = 0;
        const size_t progress_update_interval = 1024 * 1024;  // Update every 1MB
        
        std::cout << "DEBUG: Starting file copy with progress updates..." << std::endl;
        
        while (source_file_stream.good() && !source_file_stream.eof()) {
            // Check for cancellation during file copy - responsive cancellation
            if (cancelled_.load()) {
                std::cout << "DEBUG: Copy cancelled during file transfer" << std::endl;
                source_file_stream.close();
                dest_file_stream.close();
                // Remove partial file
                std::filesystem::remove(final_dest_path);
                return false;
            }
            
            source_file_stream.read(buffer.data(), buffer_size);
            std::streamsize bytes_read = source_file_stream.gcount();
            
            if (bytes_read > 0) {
                dest_file_stream.write(buffer.data(), bytes_read);
                total_copied += bytes_read;
                
                // Emit progress updates every 1MB
                if (total_copied - last_progress_update >= progress_update_interval) {
                    // Emit file progress event
                    struct FileProgressPayload {
                        const char* file_id;
                        const char* filename;
                        size_t bytes_copied;
                        size_t total_bytes;
                        size_t progress_percent;
                    };
                    
                    size_t progress_percent = (total_copied * 100) / file_size;
                    FileProgressPayload progress_payload = {
                        file_id.c_str(),
                        filename.c_str(),
                        total_copied,
                        file_size,
                        progress_percent
                    };
                    emit_event("file.progress", &progress_payload);
                    
                    last_progress_update = total_copied;
                    std::cout << "DEBUG: File progress: " << progress_percent << "% (" << total_copied << "/" << file_size << " bytes)" << std::endl;
                }
            }
        }
        
        // Close files - flush destination first to ensure all data is written
        source_file_stream.close();
        dest_file_stream.flush();  // Ensure all buffered data is written
        dest_file_stream.close();
        
        std::cout << "DEBUG: File copy completed, total copied: " << total_copied << " bytes" << std::endl;
        
        // Verify the copy was successful
        if (std::filesystem::exists(final_dest_path)) {
            size_t copied_size = std::filesystem::file_size(final_dest_path);
            std::cout << "DEBUG: Copied file size: " << copied_size << " bytes" << std::endl;
            
            if (copied_size == file_size) {
                // Update stats
                add_bytes(file_size);
                inc_files();
                
                // Add verification record for successful copy
                if (job.generate_verification_report) {
                    std::string source_hash = "size_verified";  // For now, just verify size
                    std::string dest_hash = "size_verified";
                    
                    Verification::VerificationRecord record(
                        filename,
                        source_path,
                        final_dest_path.string(),
                        file_size,
                        "size_verification",
                        source_hash,
                        dest_hash,
                        "PASS",
                        ""  // No error
                    );
                    add_verification_record(record);
                    std::cout << "DEBUG: Verification record added for: " << filename << std::endl;
                }
                
                std::cout << "DEBUG: File copy successful, stats updated" << std::endl;
                return true;
            } else {
                std::cout << "DEBUG: File size mismatch after copy: " << copied_size << " vs " << file_size << std::endl;
                add_error("File size mismatch after copy: " + source_path + " -> " + final_dest_path.string());
                return false;
            }
        } else {
            std::cout << "DEBUG: Destination file not found after copy" << std::endl;
            add_error("Destination file not found after copy: " + final_dest_path.string());
            return false;
        }
        
    } catch (const std::exception& e) {
        std::cout << "DEBUG: Exception in copy_single_file_with_progress: " << e.what() << std::endl;
        add_error("Failed to copy " + source_path + " to " + dest_path + ": " + e.what());
        return false;
    }
}

// Event emission
void EnhancedHighPerfTransferEngine::emit_event(const std::string& event_type, const void* payload) {
    if (event_sink_) {
        // Pass the actual payload data to the Python event sink
        event_sink_(event_type, payload);
    }
}

template <class F>
void EnhancedHighPerfTransferEngine::emit_event_make(const std::string& event_type, F&& fill_payload) {
    // Create and fill the payload, then emit the event
    auto payload = fill_payload();
    emit_event(event_type, &payload);
}

} // namespace EngineCore
