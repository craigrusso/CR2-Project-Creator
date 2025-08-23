#pragma once

#include <atomic>
#include <mutex>
#include <vector>
#include <string>
#include <functional>
#include <memory>

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
    void copy_to_multiple_destinations_fanout(const DataStructures::CopyJob& job, const std::vector<std::string>& files);
    bool copy_single_file(const DataStructures::CopyJob& job, const std::string& source_path, const std::string& dest_path);
    
    // Event emission
    void emit_event(const std::string& event_type, const void* payload);
    template <class F>
    void emit_event_make(const std::string& event_type, F&& fill_payload);
};

} // namespace EngineCore
