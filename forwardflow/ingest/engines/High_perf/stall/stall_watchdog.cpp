#include "stall_watchdog.hpp"

namespace StallWatchdog {

StallWatchdog::StallWatchdog(int stall_threshold_seconds, int check_interval_ms)
    : stall_threshold_seconds_(stall_threshold_seconds)
    , check_interval_ms_(check_interval_ms)
    , active_(false)
    , last_progress_ns_(0)
    , event_callback_(nullptr) {}

StallWatchdog::~StallWatchdog() {
    stop();
}

void StallWatchdog::set_event_callback(EventCallback callback) {
    event_callback_ = callback;
}

void StallWatchdog::start() {
    if (active_.load()) return;
    
    active_.store(true);
    last_progress_ns_.store(std::chrono::high_resolution_clock::now().time_since_epoch().count());
    
    watchdog_thread_ = std::thread([this]() {
        while (active_.load()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(check_interval_ms_));
            
            auto now = std::chrono::high_resolution_clock::now();
            auto last = last_progress_ns_.load();
            auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
                now - std::chrono::high_resolution_clock::time_point(std::chrono::nanoseconds(last))
            ).count();
            
            if (elapsed > stall_threshold_seconds_) {
                if (event_callback_) {
                    event_callback_("file.stalled", static_cast<int>(elapsed));
                }
                break;
            }
        }
    });
}

void StallWatchdog::stop() {
    active_.store(false);
    if (watchdog_thread_.joinable()) {
        watchdog_thread_.join();
    }
}

void StallWatchdog::update_progress() {
    last_progress_ns_.store(std::chrono::high_resolution_clock::now().time_since_epoch().count());
}

bool StallWatchdog::is_active() const {
    return active_.load();
}

int StallWatchdog::get_elapsed_seconds() const {
    auto now = std::chrono::high_resolution_clock::now();
    auto last = last_progress_ns_.load();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
        now - std::chrono::high_resolution_clock::time_point(std::chrono::nanoseconds(last))
    ).count();
    return static_cast<int>(elapsed);
}

} // namespace StallWatchdog
