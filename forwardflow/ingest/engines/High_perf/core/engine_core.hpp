#pragma once

#include <atomic>
#include <mutex>
#include <vector>
#include <string>
#include <functional>
#include <memory>
#include <chrono>
#include <thread>
#include <future>

// Include our modular components
#include "../cloud/cloud_detection.hpp"
#include "../cloud/cloud_materialization.hpp"
#include "../stall/stall_watchdog.hpp"
#include "../platform/platform_helpers.hpp"
#include "../io/cross_platform_io.hpp"
#include "../verification/verification_record.hpp"
#include "../core/data_structures.hpp"

namespace EngineCore {

/**
 * Main enhanced high-performance transfer engine
 */
class EnhancedHighPerfTransferEngine {
public:
    EnhancedHighPerfTransferEngine();
    ~EnhancedHighPerfTransferEngine() = default;
    
    // Core methods
    void set_event_sink(std::function<void(const std::string&, const void*)> sink);
    DataStructures::CopyStats copy_files(const DataStructures::CopyJob& job);
    void cancel();
    void pause();
    void resume();
    
    // Verification report methods
    void write_verification_reports(const DataStructures::CopyJob& job);
    void write_verification_reports_to_destination(const DataStructures::CopyJob& job, const std::string& dest_path);

private:
    // State
    std::atomic<bool> cancelled_{false};
    std::atomic<bool> paused_{false};
    std::function<void(const std::string&, const void*)> event_sink_;
    DataStructures::CopyStats stats_;
    std::mutex stats_mu_;
    
    // File tracking
    size_t files_processed_{0};
    
    // Verification tracking
    std::vector<Verification::VerificationRecord> verification_records_;
    std::mutex verification_mu_;
    
    // Helper methods
    void add_bytes(size_t n);
    void inc_files();
    void add_error(const std::string& e);
    void add_verification_record(const Verification::VerificationRecord& record);
    
    // File operations
    std::vector<std::string> collect_files(const std::vector<std::string>& source_paths);
    void copy_to_single_destination(const DataStructures::CopyJob& job, const std::vector<std::string>& files);
    void copy_to_multiple_destinations(const DataStructures::CopyJob& job, const std::vector<std::string>& files);
    
    // New methods that accept filtered destination lists
    void copy_to_single_destination_with_destinations(const DataStructures::CopyJob& job, const std::vector<std::string>& files, const std::vector<std::string>& valid_destinations);
    void copy_to_multiple_destinations_with_destinations(const DataStructures::CopyJob& job, const std::vector<std::string>& files, const std::vector<std::string>& valid_destinations);
    void copy_to_multiple_destinations_fanout(const DataStructures::CopyJob& job, const std::vector<std::string>& files);
    bool copy_single_file(const DataStructures::CopyJob& job, const std::string& source_path, const std::string& dest_path);
    
    // High-performance parallel multi-destination methods
    bool copy_file_parallel_multi_dest(const DataStructures::CopyJob& job, const std::string& source_path, const std::vector<std::string>& dest_paths);
    
    // Per-destination tracking structures
    struct DestinationStats {
        std::string path;
        std::atomic<size_t> bytes_copied{0};
        std::atomic<size_t> files_completed{0};
        std::chrono::steady_clock::time_point start_time;
        std::chrono::steady_clock::time_point last_update;
        std::atomic<double> current_speed_mbps{0.0};
        std::atomic<double> peak_speed_mbps{0.0};
        std::mutex stats_mutex;
        
        // Make movable but not copyable
        DestinationStats() = default;
        DestinationStats(const DestinationStats&) = delete;
        DestinationStats& operator=(const DestinationStats&) = delete;
        DestinationStats(DestinationStats&& other) noexcept 
            : path(std::move(other.path))
            , bytes_copied(other.bytes_copied.load())
            , files_completed(other.files_completed.load())
            , start_time(other.start_time)
            , last_update(other.last_update)
            , current_speed_mbps(other.current_speed_mbps.load())
            , peak_speed_mbps(other.peak_speed_mbps.load())
            , stats_mutex() {}
        DestinationStats& operator=(DestinationStats&& other) noexcept {
            if (this != &other) {
                path = std::move(other.path);
                bytes_copied = other.bytes_copied.load();
                files_completed = other.files_completed.load();
                start_time = other.start_time;
                last_update = other.last_update;
                current_speed_mbps = other.current_speed_mbps.load();
                peak_speed_mbps = other.peak_speed_mbps.load();
            }
            return *this;
        }
    };
    
    std::vector<DestinationStats> dest_stats_;
    std::mutex dest_stats_mutex_;
    
    // Disk space validation
    bool check_disk_space(const std::string& destination_path, size_t required_bytes);
    size_t get_available_disk_space(const std::string& path);
    
    // Event emission
    void emit_event(const std::string& event_type, const void* payload);
    
    template <class F>
    void emit_event_make(const std::string& event_type, F&& fill_payload);

public:
    // Specific event emission methods that convert C++ structs to Python-readable data
    void emit_dest_progress(const DataStructures::DestProgressPayload& payload);
    void emit_job_progress(size_t bytes_copied, size_t total_bytes, int files_completed, int total_files, double elapsed, double speed_mbps);
    void emit_file_completed(const std::string& filename, size_t bytes);
};

} // namespace EngineCore
