#pragma once

#include <string>
#include <vector>
#include <atomic>
#include <functional>
#include <chrono>
#include <unordered_map>
#include <mutex>

namespace DataStructures {

/**
 * Tuned parameters for each destination
 */
struct TunedParams {
    int block_size;        // bytes
    int files_in_flight;   // parallel files per dest
    int ranges_per_file;   // segments per file
    bool use_direct_io;
    
    TunedParams() : block_size(4 * 1024 * 1024), files_in_flight(1), 
                   ranges_per_file(1), use_direct_io(false) {}
};

/**
 * Copy statistics
 */
struct CopyStats {
    int total_files = 0;
    int copied_files = 0;
    size_t total_bytes = 0;
    size_t copied_bytes = 0;
    double start_time = 0.0;
    double end_time = 0.0;
    double speed_mbps = 0.0;
    double data_mbps = 0.0;  // data speed vs wall time
    double data_elapsed_s = 0.0;  // data transfer time
    std::vector<std::string> errors;
    int hash_verifications = 0;
    int hash_failures = 0;
    
    double duration() const { return end_time - start_time; }
    double success_rate() const { 
        return total_files > 0 ? (copied_files * 100.0) / total_files : 0.0; 
    }
};

/**
 * Enhanced copy job with multi-destination support
 */
struct CopyJob {
    std::vector<std::string> source_paths;
    std::vector<std::string> destination_paths;  // Now supports multiple destinations
    size_t block_size = 4 * 1024 * 1024;    // ≥ 4 MB default
    int    thread_count = 0;                // legacy, keep for compat
    bool   use_direct_io = false;           // default buffered
    bool   verify_integrity = false;
    std::string hash_algorithm = "xxhash64";
    int    mtu_size = 0;
    int    socket_buffer_size = 0;
    std::function<void(const std::string&, const void*)> progress_callback;
    std::atomic<bool>* cancel_event = nullptr;
    std::atomic<bool>* pause_event = nullptr;
    bool   adaptive_parameters = true;
    size_t large_file_threshold = 256 * 1024 * 1024;
    
    // Separate concurrency knobs
    int    files_in_flight  = 1;            // files copying at once
    int    ranges_per_file  = 1;            // parallel ranges inside one file
    
    // Multi-destination settings
    std::string preset = "auto";            // auto, usb, network, custom
    std::string verify_mode = "FAST";       // FAST, STREAM_VERIFY, READBACK_VERIFY
    std::vector<TunedParams> per_dest_params;  // Auto-computed per destination
    
    // Verification report generation
    bool   generate_verification_report = true;
    std::string job_id = "";                // For report identification
    std::string reports_folder_name = "_ForwardFlow_verification_Reports";  // Configurable reports folder name
    
    // Cloud source detection
    bool   cloud_source = false;            // Indicates if source is cloud-backed
};

/**
 * Destination progress payload for UI updates
 */
struct DestProgressPayload {
    size_t dest_index;
    const char* dest_path;
    const char* transfer_type;
    size_t bytes_copied;
    size_t total_bytes;
    double current_speed_mbps;
    double peak_speed_mbps;
    double elapsed_time;
    size_t completed_files;
    size_t total_files;
};

/**
 * Progress gate for throttling events
 */
struct ProgressGate {
    std::mutex mu;
    std::unordered_map<std::string, int64_t> last_ns;
    static int64_t now_ns();
    bool should_emit(const std::string& key, int64_t interval_ns = 100'000'000);
};

} // namespace DataStructures
