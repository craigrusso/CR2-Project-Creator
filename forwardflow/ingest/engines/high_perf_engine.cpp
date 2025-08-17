#include <Python.h>
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

// macOS doesn't have sendfile, so we'll use efficient alternatives
#ifdef __APPLE__
    #include <copyfile.h>
    #define HAS_COPYFILE 1
#else
    #include <sys/sendfile.h>
    #define HAS_SENDFILE 1
#endif

namespace py = pybind11;

class HighPerfTransferEngine {
private:
    std::atomic<bool> cancelled_{false};
    std::atomic<bool> paused_{false};
    std::function<void(const std::string&, const py::dict&)> event_sink_;
    
    // Performance tuning constants
    static constexpr size_t OPTIMAL_CHUNK_SIZE = 256 * 1024 * 1024;  // 256MB chunks
    static constexpr size_t MIN_CHUNK_SIZE = 64 * 1024 * 1024;       // 64MB minimum
    static constexpr size_t MAX_WORKERS = 32;                         // Maximum parallel workers
    static constexpr size_t BUFFER_SIZE = 16 * 1024 * 1024;          // 16MB buffer for small files
    
public:
    HighPerfTransferEngine() = default;
    
    void set_event_sink(std::function<void(const std::string&, const py::dict&)> sink) {
        event_sink_ = sink;
    }
    
    void cancel() { cancelled_ = true; }
    void pause() { paused_ = true; }
    void resume() { paused_ = false; }
    
    // High-performance file transfer using zero-copy techniques
    bool transfer_file(const std::string& src_path, const std::string& dst_path, 
                      size_t file_size, const std::string& file_id) {
        
        int src_fd = open(src_path.c_str(), O_RDONLY);
        if (src_fd == -1) {
            emit_event("file.failed", {
                {"file_id", file_id},
                {"error", "Failed to open source file: " + std::string(strerror(errno))}
            });
            return false;
        }
        
        int dst_fd = open(dst_path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (dst_fd == -1) {
            close(src_fd);
            emit_event("file.failed", {
                {"file_id", file_id},
                {"error", "Failed to open destination file: " + std::string(strerror(errno))}
            });
            return false;
        }
        
        // Pre-allocate file size for better performance
        if (ftruncate(dst_fd, file_size) == -1) {
            close(src_fd);
            close(dst_fd);
            emit_event("file.failed", {
                {"file_id", file_id},
                {"error", "Failed to pre-allocate destination file"}
            });
            return false;
        }
        
        bool success = false;
        
        if (file_size >= OPTIMAL_CHUNK_SIZE) {
            // Use zero-copy sendfile for large files
            success = transfer_large_file_zero_copy(src_fd, dst_fd, file_size, file_id);
        } else if (file_size >= MIN_CHUNK_SIZE) {
            // Use memory-mapped I/O for medium files
            success = transfer_medium_file_mmap(src_fd, dst_fd, file_size, file_id);
        } else {
            // Use optimized buffered I/O for small files
            success = transfer_small_file_buffered(src_fd, dst_fd, file_size, file_id);
        }
        
        close(src_fd);
        close(dst_fd);
        
        if (success) {
            emit_event("file.completed", {
                {"file_id", file_id},
                {"bytes", file_size},
                {"total", file_size}
            });
        }
        
        return success;
    }
    
private:
    // Zero-copy transfer using sendfile for maximum performance
    bool transfer_large_file_zero_copy(int src_fd, int dst_fd, size_t file_size, 
                                     const std::string& file_id) {
        size_t total_copied = 0;
        size_t chunk_size = OPTIMAL_CHUNK_SIZE;
        
        while (total_copied < file_size && !cancelled_) {
            if (paused_) {
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
                continue;
            }
            
            size_t remaining = file_size - total_copied;
            size_t to_copy = std::min(chunk_size, remaining);
            
            ssize_t copied = sendfile(dst_fd, src_fd, nullptr, to_copy);
            
            if (copied == -1) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    // Non-blocking I/O, try smaller chunk
                    chunk_size = std::max(MIN_CHUNK_SIZE, chunk_size / 2);
                    continue;
                }
                emit_event("file.failed", {
                    {"file_id", file_id},
                    {"error", "sendfile failed: " + std::string(strerror(errno))}
                });
                return false;
            }
            
            total_copied += copied;
            
            // Emit progress
            emit_event("file.progress", {
                {"file_id", file_id},
                {"bytes", total_copied},
                {"total", file_size}
            });
            
            // Adaptive chunk sizing based on performance
            if (copied == static_cast<ssize_t>(to_copy)) {
                chunk_size = std::min(OPTIMAL_CHUNK_SIZE, chunk_size * 2);
            }
        }
        
        return total_copied == file_size;
    }
    
    // Memory-mapped I/O for medium files
    bool transfer_medium_file_mmap(int src_fd, int dst_fd, size_t file_size, 
                                  const std::string& file_id) {
        void* src_map = mmap(nullptr, file_size, PROT_READ, MAP_PRIVATE, src_fd, 0);
        if (src_map == MAP_FAILED) {
            emit_event("file.failed", {
                {"file_id", file_id},
                {"error", "Failed to mmap source file"}
            });
            return false;
        }
        
        void* dst_map = mmap(nullptr, file_size, PROT_WRITE, MAP_SHARED, dst_fd, 0);
        if (dst_map == MAP_FAILED) {
            munmap(src_map, file_size);
            emit_event("file.failed", {
                {"file_id", file_id},
                {"error", "Failed to mmap destination file"}
            });
            return false;
        }
        
        // Copy data using optimized memcpy
        memcpy(dst_map, src_map, file_size);
        
        // Ensure data is written to disk
        msync(dst_map, file_size, MS_SYNC);
        
        munmap(src_map, file_size);
        munmap(dst_map, file_size);
        
        emit_event("file.progress", {
            {"file_id", file_id},
            {"bytes", file_size},
            {"total", file_size}
        });
        
        return true;
    }
    
    // Optimized buffered I/O for small files
    bool transfer_small_file_buffered(int src_fd, int dst_fd, size_t file_size, 
                                     const std::string& file_id) {
        std::vector<char> buffer(BUFFER_SIZE);
        size_t total_copied = 0;
        
        while (total_copied < file_size && !cancelled_) {
            if (paused_) {
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
                continue;
            }
            
            size_t remaining = file_size - total_copied;
            size_t to_read = std::min(buffer.size(), remaining);
            
            ssize_t bytes_read = read(src_fd, buffer.data(), to_read);
            if (bytes_read <= 0) {
                emit_event("file.failed", {
                    {"file_id", file_id},
                    {"error", "Failed to read source file"}
                });
                return false;
            }
            
            ssize_t bytes_written = write(dst_fd, buffer.data(), bytes_read);
            if (bytes_written != bytes_read) {
                emit_event("file.failed", {
                    {"file_id", file_id},
                    {"error", "Failed to write destination file"}
                });
                return false;
            }
            
            total_copied += bytes_read;
            
            emit_event("file.progress", {
                {"file_id", file_id},
                {"file_id", file_id},
                {"bytes", total_copied},
                {"total", file_size}
            });
        }
        
        return total_copied == file_size;
    }
    
    void emit_event(const std::string& event_type, const py::dict& payload) {
        if (event_sink_) {
            event_sink_(event_type, payload);
        }
    }
};

// Python bindings
PYBIND11_MODULE(high_perf_engine, m) {
    py::class_<HighPerfTransferEngine>(m, "HighPerfTransferEngine")
        .def(py::init<>())
        .def("set_event_sink", &HighPerfTransferEngine::set_event_sink)
        .def("transfer_file", &HighPerfTransferEngine::transfer_file)
        .def("cancel", &HighPerfTransferEngine::cancel)
        .def("pause", &HighPerfTransferEngine::pause)
        .def("resume", &HighPerfTransferEngine::resume);
}
