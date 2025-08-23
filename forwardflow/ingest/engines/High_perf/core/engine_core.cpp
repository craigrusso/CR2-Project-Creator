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
        // Emit job started event
        emit_event("job.started", nullptr);
        
        // Collect all files to copy
        auto files = collect_files(job.source_paths);
        stats_.total_files = files.size();
        
        // Emit job progress event with total files
        emit_event("job.progress", nullptr);
        
        // Determine copy strategy based on destination count
        if (job.destination_paths.size() == 1) {
            copy_to_single_destination(job, files);
        } else {
            copy_to_multiple_destinations(job, files);
        }
        
        // Emit job completed event
        emit_event("job.completed", nullptr);
        
    } catch (const std::exception& e) {
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
    // Implementation would recursively collect files from source paths
    // For now, just return the source paths as-is
    return source_paths;
}

void EnhancedHighPerfTransferEngine::copy_to_single_destination(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    for (const auto& file : files) {
        if (cancelled_.load()) break;
        
        // Emit file started event
        emit_event("file.started", nullptr);
        
        for (const auto& dest : job.destination_paths) {
            if (copy_single_file(job, file, dest)) {
                inc_files();
                
                // Emit file completed event
                emit_event("file.completed", nullptr);
            }
        }
    }
}

void EnhancedHighPerfTransferEngine::copy_to_multiple_destinations(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    // Use fan-out strategy for multiple destinations
    copy_to_multiple_destinations_fanout(job, files);
}

void EnhancedHighPerfTransferEngine::copy_to_multiple_destinations_fanout(const DataStructures::CopyJob& job, const std::vector<std::string>& files) {
    for (const auto& file : files) {
        if (cancelled_.load()) break;
        
        // Emit file started event
        emit_event("file.started", nullptr);
        
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
                
                // Emit file completed event
                emit_event("file.completed", nullptr);
            }
        }
    }
}

bool EnhancedHighPerfTransferEngine::copy_single_file(const DataStructures::CopyJob& job, const std::string& source_path, const std::string& dest_path) {
    try {
        // Basic file copy implementation
        // In the real implementation, this would use the optimized copy methods
        std::filesystem::copy_file(source_path, dest_path, std::filesystem::copy_options::overwrite_existing);
        
        // Get file size for stats
        size_t file_size = std::filesystem::file_size(source_path);
        add_bytes(file_size);
        
        return true;
    } catch (const std::exception& e) {
        add_error("Failed to copy " + source_path + " to " + dest_path + ": " + e.what());
        return false;
    }
}

// Event emission
void EnhancedHighPerfTransferEngine::emit_event(const std::string& event_type, const void* payload) {
    if (event_sink_) {
        event_sink_(event_type, payload);
    }
}

template <class F>
void EnhancedHighPerfTransferEngine::emit_event_make(const std::string& event_type, F&& fill_payload) {
    // Simplified version for now
    emit_event(event_type, nullptr);
}

} // namespace EngineCore
