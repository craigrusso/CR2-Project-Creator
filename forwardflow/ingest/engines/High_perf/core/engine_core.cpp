#include "engine_core.hpp"
#include <chrono>
#include <iostream>

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
        
        // Emit job started event with proper payload
        struct JobStartedPayload {
            const char* job_id;
            size_t total_bytes;
            size_t total_files;
        };
        JobStartedPayload job_started_payload = {"", stats_.total_bytes, static_cast<size_t>(stats_.total_files)};
        emit_event("job.started", &job_started_payload);
        
        // Emit job progress event with total files
        emit_event("job.progress", nullptr);
        
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
        // Use verification manager to write reports to specific destination
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
        if (cancelled_.load()) break;
        
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
    }
}

void EnhancedHighPerfTransferEngine::copy_to_multiple_destinations(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    // Use fan-out strategy for multiple destinations
    copy_to_multiple_destinations_fanout(job, files);
}

void EnhancedHighPerfTransferEngine::copy_to_multiple_destinations_fanout(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    for (const auto& file : files) {
        if (cancelled_.load()) break;
        
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
        
        // This would call the actual copy_file_to_many implementation
        // For now, just copy to each destination individually
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
        
        // Get source file size for stats
        size_t file_size = std::filesystem::file_size(source_path);
        std::cout << "DEBUG: Source file size: " << file_size << " bytes" << std::endl;
        
        // Create destination path by combining dest_dir with source filename
        std::filesystem::path source_file = std::filesystem::path(source_path).filename();
        std::filesystem::path final_dest_path = dest_dir / source_file;
        std::cout << "DEBUG: Final destination path: " << final_dest_path.string() << std::endl;
        
        // Copy the file
        std::cout << "DEBUG: Starting file copy..." << std::endl;
        std::filesystem::copy_file(source_path, final_dest_path, std::filesystem::copy_options::overwrite_existing);
        std::cout << "DEBUG: File copy completed" << std::endl;
        
        // Verify the copy was successful
        if (std::filesystem::exists(final_dest_path)) {
            size_t copied_size = std::filesystem::file_size(final_dest_path);
            std::cout << "DEBUG: Copied file size: " << copied_size << " bytes" << std::endl;
            
            if (copied_size == file_size) {
                // Update stats
                add_bytes(file_size);
                inc_files();
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
        std::cout << "DEBUG: Exception in copy_single_file: " << e.what() << std::endl;
        add_error("Failed to copy " + source_path + " to " + dest_path + ": " + e.what());
        return false;
    }
}

// Event emission
void EnhancedHighPerfTransferEngine::emit_event(const std::string& event_type, const void* payload) {
    if (event_sink_) {
        // For now, emit events without payloads to avoid PyCapsule issues
        // The Python side will handle the event types and update progress accordingly
        event_sink_(event_type, nullptr);
    }
}

template <class F>
void EnhancedHighPerfTransferEngine::emit_event_make(const std::string& event_type, F&& fill_payload) {
    // Simplified version for now
    emit_event(event_type, nullptr);
}

} // namespace EngineCore
