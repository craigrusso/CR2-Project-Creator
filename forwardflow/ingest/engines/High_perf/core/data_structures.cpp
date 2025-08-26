#include "data_structures.hpp"
#include <chrono>

namespace DataStructures {

int64_t ProgressGate::now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()).count();
}

bool ProgressGate::should_emit(const std::string& key, int64_t interval_ns) {
    std::lock_guard<std::mutex> lock(mu);
    auto now = now_ns();
    auto it = last_ns.find(key);
    
    if (it == last_ns.end() || (now - it->second) >= interval_ns) {
        last_ns[key] = now;
        return true;
    }
    
    return false;
}

// Enhanced data structures use inline constructors defined in header

} // namespace DataStructures
