#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <thread>
#include <future>
#include <atomic>
#include <chrono>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <errno.h>
#include <string.h>
#include <filesystem>
#include <algorithm>
#include <memory>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <random>
#include <iomanip>
#include <sstream>

// Platform-specific includes
#ifdef _WIN32
    #include <windows.h>
    #include <winioctl.h>
    #include <io.h>
    #include <direct.h>
#elif defined(__APPLE__)
    #include <copyfile.h>
    #include <sys/param.h>
    #include <sys/mount.h>
    #include <sys/socket.h>
    #include <net/if.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <sys/ioctl.h>
#else
    #include <sys/sendfile.h>
    #include <linux/fs.h>
    #include <linux/fiemap.h>
    #include <sys/socket.h>
    #include <net/if.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <sys/ioctl.h>
    #include <linux/sockios.h>
#endif

// Hash libraries
#include <openssl/md5.h>
#include <openssl/sha.h>
#include <xxhash.h>

namespace py = pybind11;
namespace fs = std::filesystem;

// Data structures
struct BandwidthTest {
    double write_speed;
    double read_speed;
    double avg_speed;
};

struct CopyStats {
    int total_files = 0;
    int copied_files = 0;
    size_t total_bytes = 0;
    size_t copied_bytes = 0;
    double start_time = 0.0;
    double end_time = 0.0;
    double speed_mbps = 0.0;
    std::vector<std::string> errors;
    int hash_verifications = 0;
    int hash_failures = 0;
    
    double duration() const { return end_time - start_time; }
    double success_rate() const { 
        return total_files > 0 ? (copied_files * 100.0) / total_files : 0.0; 
    }
};

struct CopyJob {
    std::vector<std::string> source_paths;
    std::vector<std::string> destination_paths;
    size_t block_size = 1024 * 1024;  // 1MB default
    int thread_count = 0;  // 0 = auto-detect
    bool use_direct_io = true;
    bool verify_integrity = true;
    std::string hash_algorithm = "xxhash64";
    int mtu_size = 0;  // 0 = auto-detect
    int socket_buffer_size = 0;  // 0 = auto-detect
    std::function<void(const std::string&, const py::dict&)> progress_callback;
    std::atomic<bool>* cancel_event = nullptr;
    std::atomic<bool>* pause_event = nullptr;
    bool adaptive_parameters = true;
    size_t large_file_threshold = 100 * 1024 * 1024;  // 100MB
};

// Cross-platform I/O operations
class CrossPlatformIO {
public:
    static size_t get_optimal_block_size() {
        #ifdef _WIN32
            return 64 * 1024;  // 64KB for Windows
        #else
            return 1024 * 1024;  // 1MB for Unix-like systems
        #endif
    }
    
    static int get_optimal_thread_count() {
        int cores = std::thread::hardware_concurrency();
        return std::min(32, cores * 2);
    }
    
    static int open_direct_read(const std::string& path) {
        try {
            #ifdef _WIN32
                HANDLE handle = CreateFileA(
                    path.c_str(),
                    GENERIC_READ,
                    FILE_SHARE_READ,
                    nullptr,
                    OPEN_EXISTING,
                    FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN,
                    nullptr
                );
                return reinterpret_cast<int>(handle);
            #elif defined(__APPLE__)
                int fd = open(path.c_str(), O_RDONLY);
                if (fd != -1) {
                    fcntl(fd, F_NOCACHE, 1);
                }
                return fd;
            #else
                return open(path.c_str(), O_RDONLY | O_DIRECT);
            #endif
        } catch (...) {
            return -1;
        }
    }
    
    static int open_direct_write(const std::string& path, size_t size = 0) {
        try {
            #ifdef _WIN32
                HANDLE handle = CreateFileA(
                    path.c_str(),
                    GENERIC_WRITE,
                    0,
                    nullptr,
                    CREATE_ALWAYS,
                    FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN,
                    nullptr
                );
                if (handle != INVALID_HANDLE_VALUE && size > 0) {
                    LARGE_INTEGER li;
                    li.QuadPart = size;
                    SetFilePointerEx(handle, li, nullptr, FILE_BEGIN);
                    SetEndOfFile(handle);
                }
                return reinterpret_cast<int>(handle);
            #elif defined(__APPLE__)
                int fd = open(path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
                if (fd != -1) {
                    fcntl(fd, F_NOCACHE, 1);
                    if (size > 0) {
                        ftruncate(fd, size);
                    }
                }
                return fd;
            #else
                int fd = open(path.c_str(), O_WRONLY | O_CREAT | O_TRUNC | O_DIRECT, 0644);
                if (fd != -1 && size > 0) {
                    // Use fallocate if available
                    #ifdef _GNU_SOURCE
                        fallocate(fd, 0, 0, size);
                    #endif
                }
                return fd;
            #endif
        } catch (...) {
            return -1;
        }
    }
    
    static void close_handle(int handle) {
        try {
            #ifdef _WIN32
                CloseHandle(reinterpret_cast<HANDLE>(handle));
            #else
                close(handle);
            #endif
        } catch (...) {}
    }
    
    static ssize_t read_direct(int handle, void* buffer, size_t size) {
        try {
            #ifdef _WIN32
                DWORD bytes_read;
                BOOL result = ReadFile(
                    reinterpret_cast<HANDLE>(handle),
                    buffer,
                    static_cast<DWORD>(size),
                    &bytes_read,
                    nullptr
                );
                return result ? bytes_read : -1;
            #else
                return read(handle, buffer, size);
            #endif
        } catch (...) {
            return -1;
        }
    }
    
    static ssize_t write_direct(int handle, const void* buffer, size_t size) {
        try {
            #ifdef _WIN32
                DWORD bytes_written;
                BOOL result = WriteFile(
                    reinterpret_cast<HANDLE>(handle),
                    buffer,
                    static_cast<DWORD>(size),
                    &bytes_written,
                    nullptr
                );
                return result ? bytes_written : -1;
            #else
                return write(handle, buffer, size);
            #endif
        } catch (...) {
            return -1;
        }
    }
};

// Bandwidth detection
class BandwidthDetector {
public:
    static BandwidthTest test_disk_bandwidth(const std::string& test_dir = "") {
        BandwidthTest result = {100.0, 100.0, 100.0};  // Default fallback
        
        std::string temp_dir = test_dir.empty() ? fs::temp_directory_path().string() : test_dir;
        std::string test_file = temp_dir + "/bandwidth_test_" + std::to_string(std::time(nullptr)) + ".tmp";
        size_t test_size = 100 * 1024 * 1024;  // 100MB test
        
        try {
            // Write test
            auto start_time = std::chrono::high_resolution_clock::now();
            {
                std::ofstream file(test_file, std::ios::binary);
                std::vector<char> buffer(1024 * 1024, 0);  // 1MB buffer
                for (size_t i = 0; i < test_size / buffer.size(); ++i) {
                    file.write(buffer.data(), buffer.size());
                }
            }
            auto write_end = std::chrono::high_resolution_clock::now();
            auto write_duration = std::chrono::duration<double>(write_end - start_time).count();
            result.write_speed = (test_size / (1024.0 * 1024.0)) / write_duration;
            
            // Read test
            start_time = std::chrono::high_resolution_clock::now();
            {
                std::ifstream file(test_file, std::ios::binary);
                std::vector<char> buffer(1024 * 1024);
                while (file.read(buffer.data(), buffer.size())) {
                    // Just read, don't process
                }
            }
            auto read_end = std::chrono::high_resolution_clock::now();
            auto read_duration = std::chrono::duration<double>(read_end - start_time).count();
            result.read_speed = (test_size / (1024.0 * 1024.0)) / read_duration;
            
            result.avg_speed = (result.write_speed + result.read_speed) / 2.0;
            
            // Cleanup
            fs::remove(test_file);
            
        } catch (...) {
            // Keep default values
        }
        
        return result;
    }
    
    static std::map<std::string, int> get_optimal_parameters(double bandwidth_mbps = 0.0) {
        std::map<std::string, int> params;
        
        if (bandwidth_mbps <= 0) {
            auto test = test_disk_bandwidth();
            bandwidth_mbps = test.avg_speed;
        }
        
        // Adaptive parameters based on bandwidth
        if (bandwidth_mbps > 1000) {  // High-speed storage
            params["block_size"] = 2 * 1024 * 1024;  // 2MB
            params["thread_count"] = std::min(16, CrossPlatformIO::get_optimal_thread_count());
        } else if (bandwidth_mbps > 100) {  // SSD
            params["block_size"] = 1024 * 1024;  // 1MB
            params["thread_count"] = std::min(8, CrossPlatformIO::get_optimal_thread_count());
        } else {  // HDD or network
            params["block_size"] = 512 * 1024;  // 512KB
            params["thread_count"] = std::min(4, CrossPlatformIO::get_optimal_thread_count());
        }
        
        params["use_direct_io"] = bandwidth_mbps > 50 ? 1 : 0;
        params["large_file_threshold"] = bandwidth_mbps > 100 ? 50 * 1024 * 1024 : 100 * 1024 * 1024;
        
        return params;
    }
};

// Hash calculation
class HashCalculator {
public:
    static std::string calculate_file_hash(const std::string& file_path, const std::string& algorithm = "xxhash64") {
        std::ifstream file(file_path, std::ios::binary);
        if (!file) return "";
        
        if (algorithm == "xxhash64") {
            XXH64_state_t* state = XXH64_createState();
            XXH64_reset(state, 0);
            
            std::vector<char> buffer(1024 * 1024);  // 1MB buffer
            while (file.read(buffer.data(), buffer.size())) {
                XXH64_update(state, buffer.data(), file.gcount());
            }
            
            XXH64_hash_t hash = XXH64_digest(state);
            XXH64_freeState(state);
            
            std::stringstream ss;
            ss << std::hex << std::setfill('0') << std::setw(16) << hash;
            return ss.str();
            
        } else if (algorithm == "sha256") {
            SHA256_CTX context;
            SHA256_Init(&context);
            
            std::vector<char> buffer(1024 * 1024);
            while (file.read(buffer.data(), buffer.size())) {
                SHA256_Update(&context, reinterpret_cast<unsigned char*>(buffer.data()), file.gcount());
            }
            
            unsigned char hash[SHA256_DIGEST_LENGTH];
            SHA256_Final(hash, &context);
            
            std::stringstream ss;
            for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
                ss << std::hex << std::setfill('0') << std::setw(2) << static_cast<int>(hash[i]);
            }
            return ss.str();
            
        } else if (algorithm == "md5") {
            MD5_CTX context;
            MD5_Init(&context);
            
            std::vector<char> buffer(1024 * 1024);
            while (file.read(buffer.data(), buffer.size())) {
                MD5_Update(&context, reinterpret_cast<unsigned char*>(buffer.data()), file.gcount());
            }
            
            unsigned char hash[MD5_DIGEST_LENGTH];
            MD5_Final(hash, &context);
            
            std::stringstream ss;
            for (int i = 0; i < MD5_DIGEST_LENGTH; i++) {
                ss << std::hex << std::setfill('0') << std::setw(2) << static_cast<int>(hash[i]);
            }
            return ss.str();
        }
        
        return "";
    }
};

// Network optimization
class NetworkOptimizer {
public:
    static bool set_mtu(const std::string& interface, int mtu) {
        #ifdef _WIN32
            // Windows implementation would go here
            return false;
        #else
            int sock = socket(AF_INET, SOCK_DGRAM, 0);
            if (sock < 0) return false;
            
            struct ifreq ifr;
            strncpy(ifr.ifr_name, interface.c_str(), IFNAMSIZ - 1);
            ifr.ifr_mtu = mtu;
            
            #ifdef __APPLE__
                // macOS doesn't support SIOCSIFMTU, use system command
                std::string command = "ifconfig " + interface + " mtu " + std::to_string(mtu);
                return system(command.c_str()) == 0;
            #else
                bool result = ioctl(sock, SIOCSIFMTU, &ifr) == 0;
                close(sock);
                return result;
            #endif
        #endif
    }
    
    static bool set_socket_buffer_size(int sock, int size) {
        return setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size)) == 0 &&
               setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size)) == 0;
    }
    
    static bool enable_jumbo_frames(const std::string& interface) {
        return set_mtu(interface, 9000);
    }
};

// Main enhanced copy engine
class EnhancedHighPerfTransferEngine {
private:
    std::atomic<bool> cancelled_{false};
    std::atomic<bool> paused_{false};
    std::function<void(const std::string&, const py::dict&)> event_sink_;
    CopyStats stats_;

public:
    EnhancedHighPerfTransferEngine() = default;
    
    void set_event_sink(std::function<void(const std::string&, const py::dict&)> sink) {
        event_sink_ = sink;
    }
    
    void cancel() { cancelled_ = true; }
    void pause() { paused_ = true; }
    void resume() { paused_ = false; }
    
    CopyStats copy_files(const CopyJob& job) {
        stats_ = CopyStats();
        stats_.start_time = std::chrono::duration<double>(
            std::chrono::high_resolution_clock::now().time_since_epoch()
        ).count();
        
        cancelled_ = false;
        paused_ = false;
        
        try {
            // Apply adaptive parameters if enabled
            CopyJob optimized_job = job;
            if (job.adaptive_parameters) {
                auto bandwidth_test = BandwidthDetector::test_disk_bandwidth();
                auto optimal_params = BandwidthDetector::get_optimal_parameters(bandwidth_test.avg_speed);
                
                if (optimized_job.block_size == 0) optimized_job.block_size = optimal_params["block_size"];
                if (optimized_job.thread_count == 0) optimized_job.thread_count = optimal_params["thread_count"];
                optimized_job.use_direct_io = optimal_params["use_direct_io"] != 0;
                optimized_job.large_file_threshold = optimal_params["large_file_threshold"];
            }
            
            // Set default thread count if not specified
            if (optimized_job.thread_count == 0) {
                optimized_job.thread_count = CrossPlatformIO::get_optimal_thread_count();
            }
            
            // Set default block size if not specified
            if (optimized_job.block_size == 0) {
                optimized_job.block_size = CrossPlatformIO::get_optimal_block_size();
            }
            
            // Collect all files to copy
            std::vector<std::string> all_files = collect_files(optimized_job.source_paths);
            stats_.total_files = all_files.size();
            
            // Calculate total size
            for (const auto& file : all_files) {
                try {
                    fs::path file_path(file);
                    if (fs::is_regular_file(file_path)) {
                        stats_.total_bytes += fs::file_size(file_path);
                    }
                } catch (...) {}
            }
            
            // Handle multiple destinations
            if (optimized_job.destination_paths.size() > 1) {
                copy_to_multiple_destinations(optimized_job, all_files);
            } else {
                copy_to_single_destination(optimized_job, all_files);
            }
            
        } catch (const std::exception& e) {
            stats_.errors.push_back(std::string("Exception: ") + e.what());
        }
        
        stats_.end_time = std::chrono::duration<double>(
            std::chrono::high_resolution_clock::now().time_since_epoch()
        ).count();
        
        if (stats_.duration() > 0) {
            stats_.speed_mbps = (stats_.copied_bytes / (1024.0 * 1024.0)) / stats_.duration();
        }
        
        return stats_;
    }

private:
    std::vector<std::string> collect_files(const std::vector<std::string>& source_paths) {
        std::vector<std::string> files;
        
        for (const auto& source_path : source_paths) {
            try {
                fs::path path(source_path);
                if (fs::is_regular_file(path)) {
                    files.push_back(source_path);
                } else if (fs::is_directory(path)) {
                    for (const auto& entry : fs::recursive_directory_iterator(path)) {
                        if (fs::is_regular_file(entry)) {
                            files.push_back(entry.path().string());
                        }
                    }
                }
            } catch (...) {}
        }
        
        return files;
    }
    
    void copy_to_single_destination(const CopyJob& job, const std::vector<std::string>& files) {
        if (files.empty() || job.destination_paths.empty()) return;
        
        std::string destination = job.destination_paths[0];
        fs::create_directories(destination);
        
        // Use thread pool for copying
        std::vector<std::future<bool>> futures;
        std::mutex futures_mutex;
        
        for (const auto& source_file : files) {
            if (cancelled_) break;
            
            // Calculate destination path
            fs::path source_path(source_file);
            fs::path dest_path = fs::path(destination) / source_path.filename();
            
            // Create destination directory
            fs::create_directories(dest_path.parent_path());
            
            // Submit copy task
            {
                std::lock_guard<std::mutex> lock(futures_mutex);
                futures.emplace_back(std::async(std::launch::async, [this, &job, source_file, dest_path]() {
                    return copy_single_file(job, source_file, dest_path.string());
                }));
            }
        }
        
        // Wait for completion
        for (auto& future : futures) {
            if (cancelled_) break;
            
            try {
                if (future.get()) {
                    stats_.copied_files++;
                }
            } catch (...) {
                stats_.errors.push_back("Copy task failed");
            }
        }
    }
    
    void copy_to_multiple_destinations(const CopyJob& job, const std::vector<std::string>& files) {
        // Create destination directories
        for (const auto& dest : job.destination_paths) {
            fs::create_directories(dest);
        }
        
        // Use separate thread pools for each destination
        std::vector<std::future<void>> destination_futures;
        
        for (const auto& destination : job.destination_paths) {
            destination_futures.emplace_back(std::async(std::launch::async, [this, &job, &files, destination]() {
                copy_to_single_destination(job, files);
            }));
        }
        
        // Wait for all destinations to complete
        for (auto& future : destination_futures) {
            try {
                future.get();
            } catch (...) {
                stats_.errors.push_back("Multi-destination copy failed");
            }
        }
    }
    
    bool copy_single_file(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        try {
            fs::path source_file(source_path);
            if (!fs::is_regular_file(source_file)) return false;
            
            size_t file_size = fs::file_size(source_file);
            
            // Choose copy method based on file size
            if (file_size > job.large_file_threshold) {
                return copy_large_file(job, source_path, dest_path);
            } else {
                return copy_small_file(job, source_path, dest_path);
            }
            
        } catch (const std::exception& e) {
            stats_.errors.push_back(std::string("Copy exception: ") + e.what());
            return false;
        }
    }
    
    bool copy_large_file(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        try {
            fs::path source_file(source_path);
            size_t file_size = fs::file_size(source_file);
            
            // Split file into ranges for parallel copying
            std::vector<std::pair<size_t, size_t>> ranges = split_file_ranges(file_size, job.thread_count);
            
            // Create temporary file for assembly
            std::string temp_file = dest_path + ".tmp";
            
            std::vector<std::future<bool>> range_futures;
            
            for (const auto& range : ranges) {
                if (cancelled_) break;
                
                range_futures.emplace_back(std::async(std::launch::async, [this, &job, source_path, temp_file, range]() {
                    return copy_file_range(job, source_path, temp_file, range.first, range.second);
                }));
            }
            
            // Wait for all ranges to complete
            for (auto& future : range_futures) {
                if (cancelled_) break;
                
                if (!future.get()) {
                    return false;
                }
            }
            
            // Verify integrity if requested
            if (job.verify_integrity) {
                std::string source_hash = HashCalculator::calculate_file_hash(source_path, job.hash_algorithm);
                std::string dest_hash = HashCalculator::calculate_file_hash(temp_file, job.hash_algorithm);
                
                if (source_hash != dest_hash) {
                    stats_.hash_failures++;
                    fs::remove(temp_file);
                    return false;
                }
                stats_.hash_verifications++;
            }
            
            // Move temporary file to final destination
            fs::rename(temp_file, dest_path);
            
            stats_.copied_bytes += file_size;
            return true;
            
        } catch (const std::exception& e) {
            stats_.errors.push_back(std::string("Large file copy exception: ") + e.what());
            return false;
        }
    }
    
    bool copy_small_file(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        try {
            if (job.use_direct_io) {
                return copy_with_direct_io(job, source_path, dest_path);
            } else {
                return copy_with_buffered_io(job, source_path, dest_path);
            }
        } catch (const std::exception& e) {
            stats_.errors.push_back(std::string("Small file copy exception: ") + e.what());
            return false;
        }
    }
    
    bool copy_with_direct_io(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        fs::path source_file(source_path);
        size_t file_size = fs::file_size(source_file);
        
        int src_handle = CrossPlatformIO::open_direct_read(source_path);
        int dst_handle = CrossPlatformIO::open_direct_write(dest_path, file_size);
        
        if (src_handle == -1 || dst_handle == -1) {
            CrossPlatformIO::close_handle(src_handle);
            CrossPlatformIO::close_handle(dst_handle);
            return false;
        }
        
        try {
            std::vector<char> buffer(job.block_size);
            size_t total_copied = 0;
            
            while (total_copied < file_size && !cancelled_) {
                while (paused_) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                }
                
                size_t remaining = file_size - total_copied;
                size_t read_size = std::min(job.block_size, remaining);
                
                ssize_t bytes_read = CrossPlatformIO::read_direct(src_handle, buffer.data(), read_size);
                if (bytes_read <= 0) break;
                
                ssize_t bytes_written = CrossPlatformIO::write_direct(dst_handle, buffer.data(), bytes_read);
                if (bytes_written != bytes_read) break;
                
                total_copied += bytes_written;
                stats_.copied_bytes += bytes_written;
                
                // Emit progress event
                if (event_sink_) {
                    py::dict payload;
                    payload["bytes"] = total_copied;
                    payload["total"] = file_size;
                    event_sink_("file.progress", payload);
                }
            }
            
            CrossPlatformIO::close_handle(src_handle);
            CrossPlatformIO::close_handle(dst_handle);
            
            return total_copied == file_size;
            
        } catch (...) {
            CrossPlatformIO::close_handle(src_handle);
            CrossPlatformIO::close_handle(dst_handle);
            return false;
        }
    }
    
    bool copy_with_buffered_io(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        fs::path source_file(source_path);
        size_t file_size = fs::file_size(source_file);
        
        std::ifstream src_file(source_path, std::ios::binary);
        std::ofstream dst_file(dest_path, std::ios::binary);
        
        if (!src_file || !dst_file) return false;
        
        std::vector<char> buffer(job.block_size);
        size_t total_copied = 0;
        
        while (total_copied < file_size && !cancelled_) {
            while (paused_) {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
            
            src_file.read(buffer.data(), job.block_size);
            std::streamsize bytes_read = src_file.gcount();
            if (bytes_read <= 0) break;
            
            dst_file.write(buffer.data(), bytes_read);
            if (!dst_file) break;
            
            total_copied += bytes_read;
            stats_.copied_bytes += bytes_read;
            
            // Emit progress event
            if (event_sink_) {
                py::dict payload;
                payload["bytes"] = total_copied;
                payload["total"] = file_size;
                event_sink_("file.progress", payload);
            }
        }
        
        return total_copied == file_size;
    }
    
    bool copy_file_range(const CopyJob& job, const std::string& source_path, const std::string& dest_path, 
                        size_t start, size_t end) {
        try {
            if (job.use_direct_io) {
                return copy_range_with_direct_io(job, source_path, dest_path, start, end);
            } else {
                return copy_range_with_buffered_io(job, source_path, dest_path, start, end);
            }
        } catch (const std::exception& e) {
            stats_.errors.push_back(std::string("Range copy exception: ") + e.what());
            return false;
        }
    }
    
    bool copy_range_with_direct_io(const CopyJob& job, const std::string& source_path, const std::string& dest_path,
                                  size_t start, size_t end) {
        int src_handle = CrossPlatformIO::open_direct_read(source_path);
        int dst_handle = CrossPlatformIO::open_direct_write(dest_path);
        
        if (src_handle == -1 || dst_handle == -1) {
            CrossPlatformIO::close_handle(src_handle);
            CrossPlatformIO::close_handle(dst_handle);
            return false;
        }
        
        try {
            // Seek to start position
            #ifdef _WIN32
                LARGE_INTEGER li;
                li.QuadPart = start;
                SetFilePointerEx(reinterpret_cast<HANDLE>(src_handle), li, nullptr, FILE_BEGIN);
                li.QuadPart = start;
                SetFilePointerEx(reinterpret_cast<HANDLE>(dst_handle), li, nullptr, FILE_BEGIN);
            #else
                lseek(src_handle, start, SEEK_SET);
                lseek(dst_handle, start, SEEK_SET);
            #endif
            
            std::vector<char> buffer(job.block_size);
            size_t copied_bytes = 0;
            size_t range_size = end - start;
            
            while (copied_bytes < range_size && !cancelled_) {
                while (paused_) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                }
                
                size_t remaining = range_size - copied_bytes;
                size_t read_size = std::min(job.block_size, remaining);
                
                ssize_t bytes_read = CrossPlatformIO::read_direct(src_handle, buffer.data(), read_size);
                if (bytes_read <= 0) break;
                
                ssize_t bytes_written = CrossPlatformIO::write_direct(dst_handle, buffer.data(), bytes_read);
                if (bytes_written != bytes_read) break;
                
                copied_bytes += bytes_written;
            }
            
            CrossPlatformIO::close_handle(src_handle);
            CrossPlatformIO::close_handle(dst_handle);
            
            return copied_bytes == range_size;
            
        } catch (...) {
            CrossPlatformIO::close_handle(src_handle);
            CrossPlatformIO::close_handle(dst_handle);
            return false;
        }
    }
    
    bool copy_range_with_buffered_io(const CopyJob& job, const std::string& source_path, const std::string& dest_path,
                                    size_t start, size_t end) {
        std::ifstream src_file(source_path, std::ios::binary);
        std::fstream dst_file(dest_path, std::ios::binary | std::ios::in | std::ios::out);
        
        if (!src_file || !dst_file) return false;
        
        src_file.seekg(start);
        dst_file.seekp(start);
        
        std::vector<char> buffer(job.block_size);
        size_t copied_bytes = 0;
        size_t range_size = end - start;
        
        while (copied_bytes < range_size && !cancelled_) {
            while (paused_) {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
            
            size_t remaining = range_size - copied_bytes;
            size_t read_size = std::min(job.block_size, remaining);
            
            src_file.read(buffer.data(), read_size);
            std::streamsize bytes_read = src_file.gcount();
            if (bytes_read <= 0) break;
            
            dst_file.write(buffer.data(), bytes_read);
            if (!dst_file) break;
            
            copied_bytes += bytes_read;
        }
        
        return copied_bytes == range_size;
    }
    
    std::vector<std::pair<size_t, size_t>> split_file_ranges(size_t file_size, int thread_count) {
        std::vector<std::pair<size_t, size_t>> ranges;
        size_t chunk_size = file_size / thread_count;
        
        for (int i = 0; i < thread_count; ++i) {
            size_t start = i * chunk_size;
            size_t end = (i == thread_count - 1) ? file_size : (i + 1) * chunk_size;
            ranges.emplace_back(start, end);
        }
        
        return ranges;
    }
    
    void emit_event(const std::string& event_type, const py::dict& payload) {
        if (event_sink_) {
            event_sink_(event_type, payload);
        }
    }
};

// PyBind11 module
PYBIND11_MODULE(enhanced_high_perf_engine, m) {
    py::class_<BandwidthTest>(m, "BandwidthTest")
        .def_readwrite("write_speed", &BandwidthTest::write_speed)
        .def_readwrite("read_speed", &BandwidthTest::read_speed)
        .def_readwrite("avg_speed", &BandwidthTest::avg_speed);
    
    py::class_<CopyStats>(m, "CopyStats")
        .def_readwrite("total_files", &CopyStats::total_files)
        .def_readwrite("copied_files", &CopyStats::copied_files)
        .def_readwrite("total_bytes", &CopyStats::total_bytes)
        .def_readwrite("copied_bytes", &CopyStats::copied_bytes)
        .def_readwrite("start_time", &CopyStats::start_time)
        .def_readwrite("end_time", &CopyStats::end_time)
        .def_readwrite("speed_mbps", &CopyStats::speed_mbps)
        .def_readwrite("errors", &CopyStats::errors)
        .def_readwrite("hash_verifications", &CopyStats::hash_verifications)
        .def_readwrite("hash_failures", &CopyStats::hash_failures)
        .def("duration", &CopyStats::duration)
        .def("success_rate", &CopyStats::success_rate);
    
    py::class_<CopyJob>(m, "CopyJob")
        .def(py::init<>())
        .def_readwrite("source_paths", &CopyJob::source_paths)
        .def_readwrite("destination_paths", &CopyJob::destination_paths)
        .def_readwrite("block_size", &CopyJob::block_size)
        .def_readwrite("thread_count", &CopyJob::thread_count)
        .def_readwrite("use_direct_io", &CopyJob::use_direct_io)
        .def_readwrite("verify_integrity", &CopyJob::verify_integrity)
        .def_readwrite("hash_algorithm", &CopyJob::hash_algorithm)
        .def_readwrite("mtu_size", &CopyJob::mtu_size)
        .def_readwrite("socket_buffer_size", &CopyJob::socket_buffer_size)
        .def_readwrite("progress_callback", &CopyJob::progress_callback)
        .def_readwrite("cancel_event", &CopyJob::cancel_event)
        .def_readwrite("pause_event", &CopyJob::pause_event)
        .def_readwrite("adaptive_parameters", &CopyJob::adaptive_parameters)
        .def_readwrite("large_file_threshold", &CopyJob::large_file_threshold);
    
    py::class_<EnhancedHighPerfTransferEngine>(m, "EnhancedHighPerfTransferEngine")
        .def(py::init<>())
        .def("set_event_sink", &EnhancedHighPerfTransferEngine::set_event_sink)
        .def("copy_files", &EnhancedHighPerfTransferEngine::copy_files)
        .def("cancel", &EnhancedHighPerfTransferEngine::cancel)
        .def("pause", &EnhancedHighPerfTransferEngine::pause)
        .def("resume", &EnhancedHighPerfTransferEngine::resume);
    
    // Utility functions
    m.def("test_disk_bandwidth", &BandwidthDetector::test_disk_bandwidth);
    m.def("get_optimal_parameters", &BandwidthDetector::get_optimal_parameters);
    m.def("calculate_file_hash", &HashCalculator::calculate_file_hash);
    m.def("set_mtu", &NetworkOptimizer::set_mtu);
    m.def("set_socket_buffer_size", &NetworkOptimizer::set_socket_buffer_size);
    m.def("enable_jumbo_frames", &NetworkOptimizer::enable_jumbo_frames);
}
