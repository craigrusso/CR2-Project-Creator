#pragma once

#include <atomic>
#include <thread>
#include <chrono>
#include <functional>
#include <iostream>

namespace StallWatchdog {

/**
 * Stall watchdog that monitors file operations for stalls
 * Triggers events when operations stall beyond a threshold
 */
class StallWatchdog {
public:
    using EventCallback = std::function<void(const std::string&, int)>;
    
    StallWatchdog(int stall_threshold_seconds = 30, int check_interval_ms = 500);
    ~StallWatchdog();
    
    /**
     * Set the event callback for stall events
     */
    void set_event_callback(EventCallback callback);
    
    /**
     * Start the watchdog
     */
    void start();
    
    /**
     * Stop the watchdog
     */
    void stop();
    
    /**
     * Update progress timestamp
     */
    void update_progress();
    
    /**
     * Check if watchdog is active
     */
    bool is_active() const;
    
    /**
     * Get elapsed time since last progress
     */
    int get_elapsed_seconds() const;

private:
    int stall_threshold_seconds_;
    int check_interval_ms_;
    std::atomic<bool> active_;
    std::atomic<int64_t> last_progress_ns_;
    EventCallback event_callback_;
    std::thread watchdog_thread_;
};

} // namespace StallWatchdog
