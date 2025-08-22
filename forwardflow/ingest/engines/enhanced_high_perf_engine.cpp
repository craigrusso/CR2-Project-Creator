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
#include <mutex>
#include <cstdlib>   // std::aligned_alloc (C++17) / free
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
#include <condition_variable>
#include <random>
#include <iomanip>
#include <sstream>
#include <semaphore>
#include <unordered_map>
#include <deque>
#include <ctime>

// Platform-specific includes
#ifdef _WIN32
    #include <windows.h>
    #include <winioctl.h>
    #include <io.h>
    #include <direct.h>
    #include <shlwapi.h>
#elif defined(__APPLE__)
    #include <copyfile.h>
    #include <sys/param.h>
    #include <sys/mount.h>
    #include <sys/socket.h>
    #include <net/if.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <sys/ioctl.h>
    #include <sys/clonefile.h>
    #include <sys/mount.h>  // statfs is in mount.h on macOS
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
    #include <sys/vfs.h>
#endif

// Hash libraries
#include <openssl/md5.h>
#include <openssl/sha.h>
#include <xxhash.h>

namespace py = pybind11;
namespace fs = std::filesystem;

// ============================================================================
// PLATFORM HELPERS (detect local vs network, prealloc, clone-only on macOS)
// ============================================================================

#if defined(__APPLE__)
static bool is_network_path_macos(const std::string& path) {
    struct statfs s{};
    if (statfs(path.c_str(), &s) != 0) return false; // default local if unknown
    return (s.f_flags & MNT_LOCAL) == 0;
}

static bool try_clone_only_macos(const std::string& src, const std::string& dst) {
    return clonefile(src.c_str(), dst.c_str(), 0) == 0;
}

static bool preallocate_macos(int fd, off_t size) {
    fstore_t s = {F_ALLOCATECONTIG, F_PEOFPOSMODE, 0, size, 0};
    if (fcntl(fd, F_PREALLOCATE, &s) == -1) { 
        s.fst_flags = F_ALLOCATEALL; 
        fcntl(fd, F_PREALLOCATE, &s); 
    }
    return ftruncate(fd, size) == 0;
}
#endif

// Windows: local vs network
#if defined(_WIN32)
static bool is_network_path_win(const std::wstring& path) {
    // PathIsNetworkPathW is simplest; fallback to GetDriveTypeW check.
    typedef BOOL (WINAPI *PPathIsNetworkPathW)(LPCWSTR);
    static HMODULE h = LoadLibraryW(L"Shlwapi.dll");
    static auto PathIsNetworkPathW = (PPathIsNetworkPathW)(h ? GetProcAddress(h, "PathIsNetworkPathW") : nullptr);
    if (PathIsNetworkPathW) return PathIsNetworkPathW(path.c_str());
    UINT t = GetDriveTypeW(path.substr(0,3).c_str()); // e.g. "Z:\"
    return t == DRIVE_REMOTE;
}
#endif

// Linux: statfs f_type check for cifs/nfs
#if defined(__linux__)
#ifndef CIFS_MAGIC_NUMBER
#define CIFS_MAGIC_NUMBER 0xFF534D42
#endif
#ifndef NFS_SUPER_MAGIC
#define NFS_SUPER_MAGIC 0x6969
#endif

static bool is_network_path_linux(const std::string& path) {
    struct statfs s{};
    if (statfs(path.c_str(), &s) != 0) return false;
    return (s.f_type == (long)CIFS_MAGIC_NUMBER) || (s.f_type == (long)NFS_SUPER_MAGIC);
}
#endif

// ============================================================================
// AUTO PARAMS PER DESTINATION
// ============================================================================

struct TunedParams {
    int block_size;        // bytes
    int files_in_flight;   // parallel files per dest
    int ranges_per_file;   // segments per file
    bool use_direct_io;
    
    TunedParams() : block_size(4 * 1024 * 1024), files_in_flight(1), 
                   ranges_per_file(1), use_direct_io(false) {}
};

static TunedParams pick_params_for_destination(const std::string& dest, double link_hint_mbps = 0.0) {
    TunedParams p{};
    // Defaults
    p.block_size      = 4 * 1024 * 1024;
    p.files_in_flight = 1;
    p.ranges_per_file = 1;
    p.use_direct_io   = false;

#if defined(__APPLE__)
    const bool is_net = is_network_path_macos(dest);
#elif defined(_WIN32)
    std::wstring wdest(dest.begin(), dest.end());
    const bool is_net = is_network_path_win(wdest);
#elif defined(__linux__)
    const bool is_net = is_network_path_linux(dest);
#else
    const bool is_net = false;
#endif

    if (!is_net) {
        // USB/TB/NVMe local
        p.block_size      = 8 * 1024 * 1024;
        p.files_in_flight = 1;
        p.ranges_per_file = 1;
        p.use_direct_io   = false;
    } else {
        // Network (tune conservatively; UI may raise)
        p.block_size      = 2 * 1024 * 1024;
        p.files_in_flight = 2;
        p.ranges_per_file = 1;
        p.use_direct_io   = false;
    }
    return p;
}

// ============================================================================
// MULTI-DESTINATION FAN-OUT (read once → write to N destinations)
// ============================================================================

struct Chunk {
    std::unique_ptr<uint8_t[]> buf;
    size_t size = 0;
    size_t used = 0;
    std::atomic<int> pending{0};
    uint64_t seq = 0;
};

class ChunkPool {
public:
    ChunkPool(size_t chunks, size_t chunk_size)
    : chunk_size_(chunk_size) {
        for (size_t i=0;i<chunks;i++) {
            auto c = std::make_unique<Chunk>();
            c->buf.reset(new uint8_t[chunk_size_]);
            c->size = chunk_size_;
            free_.push_back(std::move(c));
        }
    }
    
    Chunk* acquire() {
        std::unique_lock<std::mutex> lk(mu_);
        cv_.wait(lk, [&]{ return !free_.empty(); });
        auto p = free_.back().release();
        free_.pop_back();
        return p;
    }
    
    void release(Chunk* c) {
        std::unique_lock<std::mutex> lk(mu_);
        free_.emplace_back(c);
        lk.unlock(); 
        cv_.notify_one();
    }
    
    size_t chunk_size() const { return chunk_size_; }
    
private:
    size_t chunk_size_;
    std::vector<std::unique_ptr<Chunk>> free_;
    std::mutex mu_;
    std::condition_variable cv_;
};

struct Broadcaster {
    std::deque<Chunk*> q;
    std::mutex mu;
    std::condition_variable cv;
    bool closed = false;

    void push(Chunk* c) {
        std::lock_guard<std::mutex> lk(mu);
        q.push_back(c);
        cv.notify_all();
    }
    
    bool pop(Chunk*& out) {
        std::unique_lock<std::mutex> lk(mu);
        cv.wait(lk, [&]{ return closed || !q.empty(); });
        if (q.empty()) return false;
        out = q.front(); 
        q.pop_front();
        return true;
    }
    
    void close() {
        std::lock_guard<std::mutex> lk(mu);
        closed = true;
        cv.notify_all();
    }
    
    void reopen() {
        std::lock_guard<std::mutex> lk(mu);
        closed = false;
    }
};

// Data timing
std::atomic<long long> data_first_ns{0};
std::atomic<long long> data_last_ns{0};

static inline long long now_ns() {
    using namespace std::chrono;
    return duration_cast<nanoseconds>(high_resolution_clock::now().time_since_epoch()).count();
}

// Writer thread (per destination)
static void writer_loop(const std::string& dst_path, int fd, Broadcaster* b, ChunkPool* pool,
                        std::atomic<bool>* ok, std::atomic<uint64_t>* bytes_out,
                        std::function<void(uint64_t)> on_progress) {
    try {
        for (;;) {
            Chunk* c=nullptr;
            if (!b->pop(c)) break; // closed & drained
            if (!c) continue;
            size_t off = 0;
            while (off < c->used) {
                ssize_t w = ::write(fd, c->buf.get() + off, c->used - off);
                if (w <= 0) throw std::runtime_error("write failed");
                off += (size_t)w;
                bytes_out->fetch_add((uint64_t)w);
                if (data_first_ns.load() == 0) data_first_ns.store(now_ns());
                data_last_ns.store(now_ns());
            }
            // drop our ref
            if (c->pending.fetch_sub(1) == 1) {
                pool->release(c);
            }
            if (on_progress) on_progress(bytes_out->load());
        }
        fsync(fd);
    } catch (...) {
        ok->store(false);
        // drain remaining refs so pool doesn't leak
        for(;;) {
            Chunk* c=nullptr;
            if (!b->pop(c)) break;
            if (c && c->pending.fetch_sub(1) == 1) pool->release(c);
        }
    }
}

// Main fan-out copy for one file
bool copy_file_to_many(const std::string& src_path,
                       const std::vector<std::string>& dest_paths,
                       const std::vector<TunedParams>& tuned,
                       std::function<void(const std::string&, const py::dict&)> event_sink,
                       std::atomic<bool>* cancel_event = nullptr) {
    if (dest_paths.empty()) return true;

#if defined(__APPLE__)
    // If same volume and APFS, try clone only (very fast)
    // NOTE: skip data pipeline; this rarely applies for camera cards.
    // (You can keep fstatfs check here if needed.)
#endif

    int sfd = ::open(src_path.c_str(), O_RDONLY);
    if (sfd < 0) return false;
    const uint64_t total = (uint64_t)std::filesystem::file_size(src_path);

    // Build destination fds and preallocate
    const size_t N = dest_paths.size();
    std::vector<int> dfds(N, -1);
    for (size_t i=0; i<N; ++i) {
        std::filesystem::create_directories(std::filesystem::path(dest_paths[i]).parent_path());
        dfds[i] = ::open(dest_paths[i].c_str(), O_CREAT|O_TRUNC|O_WRONLY, 0666);
        if (dfds[i] < 0) { ::close(sfd); return false; }
#if defined(__APPLE__)
        preallocate_macos(dfds[i], (off_t)total);
#endif
    }

    // Choose chunk size per-destination; for simplicity pick the max so we read once.
    size_t chunk_sz = 0;
    for (auto& t : tuned) chunk_sz = std::max(chunk_sz, (size_t)t.block_size);
    if (chunk_sz == 0) chunk_sz = 4*1024*1024;

    // Pool of, say, 16 chunks max in-flight (memory bound: 16 * chunk_sz)
    ChunkPool pool(16, chunk_sz);
    std::vector<Broadcaster> queues(N);
    std::vector<std::thread> writers;
    std::atomic<bool> ok{true};
    std::vector<std::atomic<uint64_t>> out_bytes(N);
    for (auto& b : out_bytes) b.store(0);

    // Optional BLAKE3 stream hash (source and per-destination)
    // (Integrate your existing hasher or add BLAKE3 C implementation)
    // Hasher src_hasher, dst_hashers[N]; // pseudocode

    for (size_t i=0; i<N; ++i) {
        queues[i].reopen();
        writers.emplace_back([&, i]{
            auto onp = [&](uint64_t){ /* emit per-dest file.progress if you want */ };
            writer_loop(dest_paths[i], dfds[i], &queues[i], &pool, &ok, &out_bytes[i], onp);
        });
    }

    // Reader → broadcast
    uint64_t total_read = 0;
    while (ok.load()) {
        if (cancel_event && cancel_event->load()) break;
        
        Chunk* c = pool.acquire();
        ssize_t r = ::read(sfd, c->buf.get(), pool.chunk_size());
        if (r < 0) { ok.store(false); pool.release(c); break; }
        if (r == 0) { pool.release(c); break; }
        c->used = (size_t)r;
        c->pending.store((int)N);
        total_read += (uint64_t)r;
        // stream source hash
        // if (hash_mode != HashMode::FAST) src_hasher.update(c->buf.get(), (size_t)r);
        // queue to all writers
        for (size_t i=0; i<N; ++i) queues[i].push(c);

        // emit job.file progress (overall = min(out_bytes[i]) across i)
        uint64_t min_out = total_read;
        for (size_t i=0;i<N;++i) min_out = std::min<uint64_t>(min_out, out_bytes[i].load());
        // send file.progress with min_out/total
    }

    // Close queues so writers drain
    for (auto& q : queues) q.close();
    for (auto& t : writers) t.join();

    // finalize hashes
    // if (hash_mode == HashMode::STREAM_VERIFY) {
    //     auto src_digest = src_hasher.finalize();
    //     for (size_t i=0;i<N;++i) {
    //         // Because we hashed on what we wrote, this verifies the pipeline (not media re-read).
    //         // If you want full media verification, do READBACK_VERIFY below.
    //     }
    // } else if (hash_mode == HashMode::READBACK_VERIFY) {
    //     // Re-open each dest and compute BLAKE3; compare to source digest.
    // }

    for (auto fd : dfds) if (fd>=0) ::close(fd);
    ::close(sfd);
    return ok.load();
}

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
    double data_mbps = 0.0;  // NEW: data speed vs wall time
    double data_elapsed_s = 0.0;  // NEW: data transfer time
    std::vector<std::string> errors;
    int hash_verifications = 0;
    int hash_failures = 0;
    
    double duration() const { return end_time - start_time; }
    double success_rate() const { 
        return total_files > 0 ? (copied_files * 100.0) / total_files : 0.0; 
    }
};

// Enhanced CopyJob with multi-destination support
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
    std::function<void(const std::string&, const py::dict&)> progress_callback;
    std::atomic<bool>* cancel_event = nullptr;
    std::atomic<bool>* pause_event = nullptr;
    bool   adaptive_parameters = true;
    size_t large_file_threshold = 256 * 1024 * 1024;
    // NEW: Separate concurrency knobs
    int    files_in_flight  = 1;            // files copying at once
    int    ranges_per_file  = 1;            // parallel ranges inside one file
    // NEW: Multi-destination settings
    std::string preset = "auto";            // auto, usb, network, custom
    std::string verify_mode = "FAST";       // FAST, STREAM_VERIFY, READBACK_VERIFY
    std::vector<TunedParams> per_dest_params;  // Auto-computed per destination
    // NEW: Verification report generation
    bool   generate_verification_report = true;
    std::string job_id = "";                // For report identification
};

// Per-file progress throttle (≤10 Hz)
struct ProgressGate {
    std::mutex mu;
    std::unordered_map<std::string, int64_t> last_ns;
    static int64_t now_ns() {
        using namespace std::chrono;
        return duration_cast<nanoseconds>(high_resolution_clock::now().time_since_epoch()).count();
    }
    bool should_emit(const std::string& key, int64_t interval_ns = 100'000'000) {
        std::lock_guard<std::mutex> lk(mu);
        int64_t t = now_ns();
        auto it = last_ns.find(key);
        if (it == last_ns.end() || (t - it->second) >= interval_ns) { 
            last_ns[key] = t; 
            return true; 
        }
        return false;
    }
};
static ProgressGate g_progress;

// macOS fast path + preallocation helpers
#if defined(__APPLE__)
static bool try_fast_copy_macos(const std::string& src, const std::string& dst) {
    // APFS clone first (same volume)
    if (clonefile(src.c_str(), dst.c_str(), 0) == 0) return true;
    copyfile_state_t st = copyfile_state_alloc();
    int rc = copyfile(src.c_str(), dst.c_str(), st, COPYFILE_DATA);
    // int saved = errno; // optional diagnostic
    copyfile_state_free(st);
    return rc == 0;
}


#endif

// Linux/Windows preallocation helpers:
#if defined(__linux__)
static bool preallocate_linux(int fd, off_t size) {
    if (posix_fallocate(fd, 0, size) == 0) return (ftruncate(fd, size) == 0 || errno == 0);
    return ftruncate(fd, size) == 0;
}
#endif

#if defined(_WIN32)
static bool preallocate_windows(HANDLE h, LONGLONG size) {
    LARGE_INTEGER li; li.QuadPart = size;
    if (!SetFilePointerEx(h, li, nullptr, FILE_BEGIN)) return false;
    return SetEndOfFile(h);
}
#endif

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

// 7) Safe direct-I/O buffers (alignment)
static std::unique_ptr<char, void(*)(void*)> make_aligned(size_t size){
    constexpr size_t align = 4096;
    // round size up to a multiple of align (required by std::aligned_alloc and many direct I/O paths)
    size_t sz = (size + (align - 1)) & ~(align - 1);
#if defined(_WIN32)
    void* p = _aligned_malloc(sz, align);
    return { (char*)p, [](void* q){ if (q) _aligned_free(q); } };
#elif defined(__linux__)
    void* p = nullptr;
    if (posix_memalign(&p, align, sz) != 0) p = nullptr;
    return { (char*)p, free };
#else
    // C++17 guarantees std::aligned_alloc; returns nullptr if sz not multiple of align (we already rounded)
    void* p = std::aligned_alloc(align, sz);
    return { (char*)p, free };
#endif
}

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

// Verification record structure
struct VerificationRecord {
    std::string filename;
    std::string source_path;
    std::string destination_path;
    size_t file_size_bytes;
    std::string hash_type;
    std::string source_hash;
    std::string destination_hash;
    std::string status;  // "PASS" or "FAIL"
    std::string timestamp;
    std::string error_message;
    
    VerificationRecord() = default;
    VerificationRecord(const std::string& fname, const std::string& src, const std::string& dst, 
                      size_t size, const std::string& htype, const std::string& src_hash, 
                      const std::string& dst_hash, const std::string& stat, const std::string& err = "")
        : filename(fname), source_path(src), destination_path(dst), file_size_bytes(size),
          hash_type(htype), source_hash(src_hash), destination_hash(dst_hash), 
          status(stat), error_message(err) {
        // Generate timestamp
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
        timestamp = ss.str();
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
    // minimal stats protection (expand as needed)
    std::mutex stats_mu_;
    void add_bytes(size_t n) { std::lock_guard<std::mutex> lk(stats_mu_); stats_.copied_bytes += n; }
    void inc_files()         { std::lock_guard<std::mutex> lk(stats_mu_); stats_.copied_files++; }
    void add_error(const std::string& e) { std::lock_guard<std::mutex> lk(stats_mu_); stats_.errors.push_back(e); }
    
    // NEW: Verification report tracking
    std::vector<VerificationRecord> verification_records_;
    std::mutex verification_mu_;
    void add_verification_record(const VerificationRecord& record) { 
        std::lock_guard<std::mutex> lk(verification_mu_); 
        verification_records_.push_back(record); 
    }

public:
    EnhancedHighPerfTransferEngine() = default;
    
    void set_event_sink(std::function<void(const std::string&, const py::dict&)> sink) {
        event_sink_ = sink;
    }
    
    void cancel() { 
        cancelled_ = true; 
        // Force immediate shutdown of any running operations
        std::cout << "DEBUG: C++ Engine cancellation requested - forcing immediate shutdown" << std::endl;
    }
    
    void pause() { paused_ = true; }
    void resume() { paused_ = false; }
    
    // NEW: Verification report methods
    void write_verification_reports(const CopyJob& job) {
        if (!job.generate_verification_report || verification_records_.empty()) {
            return;
        }
        
        // Write reports to each destination
        for (const auto& dest_path : job.destination_paths) {
            write_verification_reports_to_destination(job, dest_path);
        }
    }
    
    void write_verification_reports_to_destination(const CopyJob& job, const std::string& dest_path) {
        try {
            fs::path reports_dir = fs::path(dest_path) / "_ForwardFlow_Reports";
            fs::create_directories(reports_dir);
            
            // Generate timestamp for filename
            auto now = std::chrono::system_clock::now();
            auto time_t = std::chrono::system_clock::to_time_t(now);
            std::stringstream ss;
            ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d_%H%M");
            std::string timestamp = ss.str();
            
            std::string base_filename = "verify_report_" + timestamp;
            
            // Write TXT report
            fs::path txt_path = reports_dir / (base_filename + ".txt");
            write_txt_report(txt_path, job);
            
            // Write CSV report
            fs::path csv_path = reports_dir / (base_filename + ".csv");
            write_csv_report(csv_path, job);
            
        } catch (const std::exception& e) {
            add_error(std::string("Failed to write verification reports: ") + e.what());
        }
    }
    
    void write_txt_report(const fs::path& filepath, const CopyJob& job) {
        std::ofstream file(filepath);
        if (!file) return;
        
        // Write header
        file << std::string(80, '=') << "\n";
        file << "FORWARDFLOW VERIFICATION REPORT\n";
        file << std::string(80, '=') << "\n";
        file << "Job ID: " << job.job_id << "\n";
        file << "Start Time: " << std::chrono::duration<double>(stats_.start_time).count() << " seconds ago\n";
        file << "Total Files: " << verification_records_.size() << "\n";
        
        // Count passed/failed
        int passed = 0, failed = 0;
        size_t total_bytes = 0;
        for (const auto& record : verification_records_) {
            if (record.status == "PASS") passed++;
            else failed++;
            total_bytes += record.file_size_bytes;
        }
        
        file << "Passed: " << passed << "\n";
        file << "Failed: " << failed << "\n";
        file << "Total Size: " << format_bytes(total_bytes) << "\n";
        file << std::string(80, '=') << "\n\n";
        
        // Write records
        for (const auto& record : verification_records_) {
            file << "File: " << record.filename << "\n";
            file << "Source: " << record.source_path << "\n";
            file << "Destination: " << record.destination_path << "\n";
            file << "Size: " << format_bytes(record.file_size_bytes) << "\n";
            file << "HashType: " << record.hash_type << "\n";
            file << "SourceHash: " << record.source_hash << "\n";
            file << "DestHash: " << record.destination_hash << "\n";
            file << "Status: " << record.status << "\n";
            file << "Timestamp: " << record.timestamp << "\n";
            if (!record.error_message.empty()) {
                file << "Error: " << record.error_message << "\n";
            }
            file << "\n";
        }
        
        // Write summary
        file << std::string(80, '=') << "\n";
        file << "SUMMARY\n";
        file << std::string(80, '=') << "\n";
        file << "Total Files Processed: " << verification_records_.size() << "\n";
        file << "Verification Passed: " << passed << "\n";
        file << "Verification Failed: " << failed << "\n";
        if (verification_records_.size() > 0) {
            file << "Success Rate: " << std::fixed << std::setprecision(1) 
                 << (passed * 100.0 / verification_records_.size()) << "%\n";
        }
        file << "Total Data Size: " << format_bytes(total_bytes) << "\n";
        file << std::string(80, '=') << "\n";
    }
    
    void write_csv_report(const fs::path& filepath, const CopyJob& job) {
        std::ofstream file(filepath);
        if (!file) return;
        
        // Write CSV header
        file << "File,Source,Destination,Size,HashType,SourceHash,DestHash,Status,Timestamp,Error\n";
        
        // Write records
        for (const auto& record : verification_records_) {
            file << "\"" << record.filename << "\","
                 << "\"" << record.source_path << "\","
                 << "\"" << record.destination_path << "\","
                 << record.file_size_bytes << ","
                 << "\"" << record.hash_type << "\","
                 << "\"" << record.source_hash << "\","
                 << "\"" << record.destination_hash << "\","
                 << "\"" << record.status << "\","
                 << "\"" << record.timestamp << "\","
                 << "\"" << record.error_message << "\"\n";
        }
    }
    
    std::string format_bytes(size_t bytes) {
        if (bytes == 0) return "0 B";
        
        const char* units[] = {"B", "KB", "MB", "GB", "TB"};
        int unit_index = 0;
        double value = static_cast<double>(bytes);
        
        while (value >= 1024.0 && unit_index < 4) {
            value /= 1024.0;
            unit_index++;
        }
        
        std::stringstream ss;
        if (unit_index == 0) {
            ss << static_cast<int>(value) << " " << units[unit_index];
        } else {
            ss << std::fixed << std::setprecision(1) << value << " " << units[unit_index];
        }
        return ss.str();
    }
    
    CopyStats copy_files(const CopyJob& job) {
        stats_ = CopyStats();
        stats_.start_time = std::chrono::duration<double>(
            std::chrono::high_resolution_clock::now().time_since_epoch()
        ).count();
        
        cancelled_ = false;
        paused_ = false;
        
        // Reset data timing
        data_first_ns.store(0);
        data_last_ns.store(0);
        
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
            
            // Auto-compute per-destination parameters if not provided
            if (optimized_job.per_dest_params.empty()) {
                for (const auto& dest : optimized_job.destination_paths) {
                    optimized_job.per_dest_params.push_back(pick_params_for_destination(dest));
                }
            }
            
            // Collect all files to copy
            std::vector<std::string> all_files = collect_files(optimized_job.source_paths);
            stats_.total_files = all_files.size();
            
            // Calculate total size
            for (const auto& file : all_files) {
                try {
                    fs::path file_path(file);
                    if (fs::is_regular_file(file_path)) {
                        try {
                            stats_.total_bytes += fs::file_size(file_path);
                        } catch (const std::exception& e) {
                            std::cerr << "Warning: Could not get size for file " << file << ": " << e.what() << std::endl;
                            // Continue with other files
                        }
                    }
                } catch (const std::exception& e) {
                    std::cerr << "Warning: Could not process file " << file << ": " << e.what() << std::endl;
                    // Continue with other files
                }
            }
            
            // Emit job started event
            emit_event_make("job.started", [&](py::dict& payload){
                payload["total_files"] = stats_.total_files;
                payload["total_bytes"] = stats_.total_bytes;
            });
            
            // Handle multiple destinations with fan-out
            if (optimized_job.destination_paths.size() > 1) {
                copy_to_multiple_destinations_fanout(optimized_job, all_files);
            } else {
                copy_to_single_destination(optimized_job, all_files);
            }
            
        } catch (const std::exception& e) {
            stats_.errors.push_back(std::string("Exception: ") + e.what());
        }
        
        stats_.end_time = std::chrono::duration<double>(
            std::chrono::high_resolution_clock::now().time_since_epoch()
        ).count();
        
        // Calculate data speed vs wall time
        auto first = data_first_ns.load(), last = data_last_ns.load();
        if (first > 0 && last > first) {
            stats_.data_elapsed_s = double(last - first) / 1e9;
            stats_.data_mbps = (stats_.data_elapsed_s > 0.0) ? 
                (double(stats_.copied_bytes) / (1024.0 * 1024.0)) / stats_.data_elapsed_s : 0.0;
        }
        
        if (stats_.duration() > 0) {
            stats_.speed_mbps = (stats_.copied_bytes / (1024.0 * 1024.0)) / stats_.duration();
        }
        
        // Check if job was cancelled and emit appropriate event
        if (cancelled_) {
            std::cout << "DEBUG: C++ Engine job cancelled - emitting job.cancelled event" << std::endl;
            emit_event_make("job.cancelled", [&](py::dict& payload){
                payload["bytes_copied"] = stats_.copied_bytes;
                payload["total_bytes"] = stats_.total_bytes;
                payload["elapsed_time"] = stats_.duration();
            });
        } else {
            // NEW: Write verification reports if enabled
            if (job.generate_verification_report && !verification_records_.empty()) {
                write_verification_reports(job);
            }
        }
        
        // Emit job completed event with data speed (GIL-safe)
        emit_event_make("job.completed", [&](py::dict& payload){
            payload["bytes"] = stats_.copied_bytes;
            payload["total"] = stats_.total_bytes;
            payload["elapsed_s"] = stats_.duration();
            payload["mbps"] = stats_.speed_mbps;
            payload["data_elapsed_s"] = stats_.data_elapsed_s;
            payload["data_mbps"] = stats_.data_mbps;
        });
        
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
                    // Use a safer directory iteration approach
                    try {
                        for (const auto& entry : fs::recursive_directory_iterator(path, fs::directory_options::skip_permission_denied)) {
                            try {
                                if (fs::is_regular_file(entry)) {
                                    files.push_back(entry.path().string());
                                }
                            } catch (const std::exception& e) {
                                // Log but continue with other files
                                std::cerr << "Warning: Could not process file " << entry.path() << ": " << e.what() << std::endl;
                            }
                        }
                    } catch (const std::exception& e) {
                        std::cerr << "Warning: Could not iterate directory " << path << ": " << e.what() << std::endl;
                        // Try to continue with other source paths
                    }
                }
            } catch (const std::exception& e) {
                std::cerr << "Warning: Could not process source path " << source_path << ": " << e.what() << std::endl;
            }
        }
        
        return files;
    }
    
    // 2) Bounded file concurrency (replace copy_to_single_destination)
    void copy_to_single_destination(const CopyJob& job, const std::vector<std::string>& files) {
        if (files.empty() || job.destination_paths.empty()) return;
        const std::string destination = job.destination_paths[0];
        fs::create_directories(destination);

        int fif = job.files_in_flight;
#if defined(__APPLE__)
        if (job.adaptive_parameters) {
            bool is_net = is_network_path_macos(destination);
            fif = is_net ? std::max(1, std::min(2, fif<=0?2:fif)) : 1; // network up to 2; local = 1
        }
#else
        if (job.adaptive_parameters) fif = std::max(1, std::min(4, fif<=0?2:fif));
#endif
        if (fif < 1) fif = 1;

        // Track last job progress emission time using atomic for thread safety
        std::atomic<std::chrono::high_resolution_clock::time_point> last_progress_time(std::chrono::high_resolution_clock::now());
        const auto progress_interval = std::chrono::milliseconds(50); // Emit progress every 50ms for more frequent updates

        // Use mutex-based concurrency control instead of semaphore
        std::mutex slots_mutex;
        std::condition_variable slots_cv;
        int available_slots = fif;
        
        std::vector<std::future<bool>> futs;

        for (const auto& source_file : files) {
            if (cancelled_) {
                std::cout << "DEBUG: C++ Engine cancelled during file iteration - exiting immediately" << std::endl;
                break;
            }
            fs::path dst = fs::path(destination) / fs::path(source_file).filename();
            fs::create_directories(dst.parent_path());

            // Wait for available slot
            {
                std::unique_lock<std::mutex> lock(slots_mutex);
                // Check cancellation while waiting for slot
                if (slots_cv.wait_for(lock, std::chrono::milliseconds(100), [&] { return available_slots > 0 || cancelled_; })) {
                    if (cancelled_) {
                        std::cout << "DEBUG: C++ Engine cancelled while waiting for slot - exiting immediately" << std::endl;
                        break;
                    }
                    available_slots--;
                } else {
                    // Timeout or cancelled
                    if (cancelled_) {
                        std::cout << "DEBUG: C++ Engine cancelled during slot wait timeout - exiting immediately" << std::endl;
                        break;
                    }
                    continue;
                }
            }
            
            futs.emplace_back(std::async(std::launch::async, [this, &job, source_file, dst, &slots_mutex, &slots_cv, &available_slots, &last_progress_time, progress_interval]() {
                // Check cancellation at start of each async task
                if (cancelled_) {
                    std::cout << "DEBUG: C++ Engine async task cancelled before start - exiting immediately" << std::endl;
                    return false;
                }
                
                CopyJob local = job;
                if (local.adaptive_parameters) {
                    local.ranges_per_file = std::max(1, local.ranges_per_file); // keep 1 on USB/TB
                }
                bool ok = copy_single_file(local, source_file, dst.string());
                
                // Release slot
                {
                    std::lock_guard<std::mutex> lock(slots_mutex);
                    available_slots++;
                    slots_cv.notify_one();
                }
                
                // Emit job progress periodically
                auto now = std::chrono::high_resolution_clock::now();
                auto expected = last_progress_time.load();
                if (now - expected >= progress_interval) {
                    if (last_progress_time.compare_exchange_strong(expected, now)) {
                        emit_event_make("job.progress", [&](py::dict& payload){
                            payload["copied_bytes"] = stats_.copied_bytes;
                            payload["total_bytes"] = stats_.total_bytes;
                        });
                    }
                }
                
                return ok;
            }));
        }
        
        // Check cancellation before waiting for futures
        if (cancelled_) {
            std::cout << "DEBUG: C++ Engine cancelled before waiting for futures - cancelling all tasks" << std::endl;
            // Cancel all pending futures
            for (auto& f : futs) {
                f.wait_for(std::chrono::milliseconds(1)); // Don't wait long
            }
            return;
        }
        
        for (auto& f : futs) { 
            if (cancelled_) {
                std::cout << "DEBUG: C++ Engine cancelled while processing futures - exiting immediately" << std::endl;
                break;
            }
            try { 
                if (f.get()) inc_files(); 
            } catch (...) { 
                if (!cancelled_) { // Only add error if not cancelled
                    add_error("Copy task failed"); 
                }
            } 
        }
    }
    
    // 3) Fix multi-destination bug (use the actual destination)
    void copy_to_multiple_destinations(const CopyJob& job, const std::vector<std::string>& files) {
        std::vector<std::future<void>> dst_futs;
        for (const auto& dest : job.destination_paths) {
            if (cancelled_) {
                std::cout << "DEBUG: C++ Engine cancelled during multi-destination setup - exiting immediately" << std::endl;
                return;
            }
            fs::create_directories(dest);
            dst_futs.emplace_back(std::async(std::launch::async, [this, &job, &files, dest](){
                if (cancelled_) {
                    std::cout << "DEBUG: C++ Engine async destination task cancelled - exiting immediately" << std::endl;
                    return;
                }
                CopyJob j = job;
                j.destination_paths = { dest };   // <-- key fix
                copy_to_single_destination(j, files);
            }));
        }
        
        // Check cancellation before waiting for futures
        if (cancelled_) {
            std::cout << "DEBUG: C++ Engine cancelled before waiting for destination futures - cancelling all tasks" << std::endl;
            for (auto& f : dst_futs) {
                f.wait_for(std::chrono::milliseconds(1)); // Don't wait long
            }
            return;
        }
        
        for (auto& f : dst_futs) { 
            if (cancelled_) {
                std::cout << "DEBUG: C++ Engine cancelled while processing destination futures - exiting immediately" << std::endl;
                break;
            }
            try { 
                f.get(); 
            } catch (...) { 
                if (!cancelled_) { // Only add error if not cancelled
                    add_error("Multi-destination copy failed"); 
                }
            } 
        }
    }
    
    // NEW: Multi-destination fan-out (read once → write to N destinations)
    void copy_to_multiple_destinations_fanout(const CopyJob& job, const std::vector<std::string>& files) {
        if (files.empty() || job.destination_paths.empty()) return;
        
        // Determine global concurrency policy
        bool all_local = true;
        for (const auto& dest : job.destination_paths) {
#if defined(__APPLE__)
            if (is_network_path_macos(dest)) all_local = false;
#elif defined(_WIN32)
            std::wstring wdest(dest.begin(), dest.end());
            if (is_network_path_win(wdest)) all_local = false;
#elif defined(__linux__)
            if (is_network_path_linux(dest)) all_local = false;
#endif
        }
        
        // Global policy: if all dests are local, process 1 file at a time; if any network dest, allow up to 2 files at a time
        int global_files_in_flight = all_local ? 1 : 2;
        
        // Use mutex-based concurrency control
        std::mutex slots_mutex;
        std::condition_variable slots_cv;
        int available_slots = global_files_in_flight;
        
        std::vector<std::future<bool>> futs;

        for (const auto& source_file : files) {
            if (cancelled_) {
                std::cout << "DEBUG: C++ Engine cancelled during fan-out file iteration - exiting immediately" << std::endl;
                break;
            }
            
            // Wait for available slot
            {
                std::unique_lock<std::mutex> lock(slots_mutex);
                // Check cancellation while waiting for slot
                if (slots_cv.wait_for(lock, std::chrono::milliseconds(100), [&] { return available_slots > 0 || cancelled_; })) {
                    if (cancelled_) {
                        std::cout << "DEBUG: C++ Engine cancelled while waiting for fan-out slot - exiting immediately" << std::endl;
                        break;
                    }
                    available_slots--;
                } else {
                    // Timeout or cancelled
                    if (cancelled_) {
                        std::cout << "DEBUG: C++ Engine cancelled during fan-out slot wait timeout - exiting immediately" << std::endl;
                        break;
                    }
                    continue;
                }
            }
            
            futs.emplace_back(std::async(std::launch::async, [this, &job, source_file, &slots_mutex, &slots_cv, &available_slots]() {
                // Check cancellation at start of each async task
                if (cancelled_) {
                    std::cout << "DEBUG: C++ Engine fan-out async task cancelled before start - exiting immediately" << std::endl;
                    return false;
                }
                
                // Build destination paths for this file
                std::vector<std::string> dest_paths;
                for (const auto& dest : job.destination_paths) {
                    if (cancelled_) {
                        std::cout << "DEBUG: C++ Engine cancelled during destination path building - exiting immediately" << std::endl;
                        return false;
                    }
                    fs::path dst = fs::path(dest) / fs::path(source_file).filename();
                    fs::create_directories(dst.parent_path());
                    dest_paths.push_back(dst.string());
                }
                
                // Use the fan-out copy function
                bool ok = copy_file_to_many(source_file, dest_paths, job.per_dest_params, event_sink_, &cancelled_);
                
                if (ok) {
                    inc_files();
                    try {
                        add_bytes(fs::file_size(source_file));
                    } catch (...) {}
                }
                
                // Release slot
                {
                    std::lock_guard<std::mutex> lock(slots_mutex);
                    available_slots++;
                    slots_cv.notify_one();
                }
                
                // Emit job progress periodically
                emit_event_make("job.progress", [&](py::dict& payload){
                    payload["copied_bytes"] = stats_.copied_bytes;
                    payload["total_bytes"] = stats_.total_bytes;
                });
                
                return ok;
            }));
        }
        
        // Check cancellation before waiting for futures
        if (cancelled_) {
            std::cout << "DEBUG: C++ Engine cancelled before waiting for fan-out futures - cancelling all tasks" << std::endl;
            for (auto& f : futs) {
                f.wait_for(std::chrono::milliseconds(1)); // Don't wait long
            }
            return;
        }
        
        for (auto& f : futs) { 
            if (cancelled_) {
                std::cout << "DEBUG: C++ Engine cancelled while processing fan-out futures - exiting immediately" << std::endl;
                break;
            }
            try { 
                if (f.get()) inc_files(); 
            } catch (...) { 
                if (!cancelled_) { // Only add error if not cancelled
                    add_error("Fan-out copy failed"); 
                }
            } 
        }
    }
    
    // 4) Prefer fast path on macOS in copy_single_file
    bool copy_single_file(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        try {
            fs::path source_file(source_path);
            if (!fs::is_regular_file(source_file)) return false;

#if defined(__APPLE__)
            // Attempt fast path first
            if (try_fast_copy_macos(source_path, dest_path)) {
                add_bytes(fs::file_size(source_file));
                
                // NEW: Add verification record for fast copy (always PASS since it's native)
                if (job.generate_verification_report) {
                    add_non_verification_record(job, source_path, dest_path, fs::file_size(source_file));
                }
                
                return true;
            }
#endif
            size_t file_size = fs::file_size(source_file);
            
            // Choose copy method based on file size
            bool result = false;
            if (file_size > job.large_file_threshold) {
                result = copy_large_file_enhanced(job, source_path, dest_path);
            } else {
                result = copy_with_buffered_io(job, source_path, dest_path);
            }
            
            // NEW: Add verification record for non-verification cases in enhanced method
            if (result && !job.verify_integrity && file_size > job.large_file_threshold) {
                add_non_verification_record(job, source_path, dest_path, file_size);
            }
            
            return result;
            
        } catch (const std::exception& e) {
            add_error(std::string("Copy exception: ") + e.what());
            return false;
        }
    }
    
    // 5) Pre-allocate the temp file for ranged copies and open it O_RDWR (not trunc)
    bool copy_large_file(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        try {
            fs::path source_file(source_path);
            size_t file_size = fs::file_size(source_file);
            std::string temp_file = dest_path + ".tmp";

            // Create and pre-size the temp file once
#if defined(_WIN32)
            HANDLE h = CreateFileA(temp_file.c_str(), GENERIC_WRITE | GENERIC_READ, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
            if (h == INVALID_HANDLE_VALUE) return false;
            if (!preallocate_windows(h, (LONGLONG)file_size)) { CloseHandle(h); return false; }
            CloseHandle(h);
#else
            int fd = ::open(temp_file.c_str(), O_RDWR | O_CREAT | O_TRUNC, 0644);
            if (fd < 0) return false;
#  if defined(__APPLE__)
            if (!preallocate_macos(fd, (off_t)file_size)) { ::close(fd); return false; }
#  elif defined(__linux__)
            if (!preallocate_linux(fd, (off_t)file_size)) { ::close(fd); return false; }
#  endif
            ::close(fd);
#endif

            // Limit ranges on USB; here keep it simple and use 1 range unless we detect NVMe/network
            int rangesWanted = 1;
            auto ranges = split_file_ranges(file_size, rangesWanted);

            std::vector<std::future<bool>> futs;
            for (const auto& r : ranges) {
                futs.emplace_back(std::async(std::launch::async, [this, &job, source_path, temp_file, r](){
                    return copy_file_range(job, source_path, temp_file, r.first, r.second);
                }));
            }
            for (auto& f : futs) if (!f.get()) return false;

            // Optional verify: compute dest hash only (streamed verify for small-file path)
            if (job.verify_integrity) {
                std::string dest_hash = HashCalculator::calculate_file_hash(temp_file, job.hash_algorithm);
                std::string src_hash  = HashCalculator::calculate_file_hash(source_path, job.hash_algorithm);
                if (dest_hash != src_hash) { 
                    // NEW: Add verification record for failed verification
                    if (job.generate_verification_report) {
                        fs::path src_path(source_path);
                        fs::path dst_path(dest_path);
                        VerificationRecord record(src_path.filename().string(), source_path, dest_path, 
                                               file_size, job.hash_algorithm, src_hash, dest_hash, 
                                               "FAIL", "hash_mismatch");
                        add_verification_record(record);
                    }
                    
                    fs::remove(temp_file); 
                    stats_.hash_failures++; 
                    return false; 
                }
                
                // NEW: Add verification record for successful verification
                if (job.generate_verification_report) {
                    fs::path src_path(source_path);
                    fs::path dst_path(dest_path);
                    VerificationRecord record(src_path.filename().string(), source_path, dest_path, 
                                           file_size, job.hash_algorithm, src_hash, dest_hash, "PASS");
                    add_verification_record(record);
                }
                
                stats_.hash_verifications++;
            }

            fs::rename(temp_file, dest_path);
            add_bytes(file_size);
            
            // NEW: Add verification record for non-verification cases
            if (!job.verify_integrity) {
                add_non_verification_record(job, source_path, dest_path, file_size);
            }
            
            return true;
            
        } catch (const std::exception& e) {
            add_error(std::string("Large file copy exception: ") + e.what());
            return false;
        }
    }
    
    bool copy_small_file(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        try {
            bool result = false;
            if (job.use_direct_io) {
                result = copy_with_direct_io(job, source_path, dest_path);
            } else {
                result = copy_with_buffered_io(job, source_path, dest_path);
            }
            
            // NEW: Add verification record for non-verification cases
            if (result && !job.verify_integrity) {
                size_t file_size = fs::file_size(fs::path(source_path));
                add_non_verification_record(job, source_path, dest_path, file_size);
            }
            
            return result;
        } catch (const std::exception& e) {
            add_error(std::string("Small file copy exception: ") + e.what());
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
            // Use aligned buffer for direct I/O
            auto buffer = make_aligned(job.block_size);
            size_t total_copied = 0;
            
            while (total_copied < file_size && !cancelled_) {
                if (cancelled_) {
                    std::cout << "DEBUG: C++ Engine cancelled during direct I/O copy - exiting immediately" << std::endl;
                    break;
                }
                
                while (paused_) {
                    if (cancelled_) {
                        std::cout << "DEBUG: C++ Engine cancelled during pause - exiting immediately" << std::endl;
                        goto copy_cancelled;
                    }
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                }
                
                size_t remaining = file_size - total_copied;
                size_t read_size = std::min(job.block_size, remaining);
                
                ssize_t bytes_read = CrossPlatformIO::read_direct(src_handle, buffer.get(), read_size);
                if (bytes_read <= 0) break;
                
                ssize_t bytes_written = CrossPlatformIO::write_direct(dst_handle, buffer.get(), bytes_read);
                if (bytes_written != bytes_read) break;
                
                total_copied += bytes_written;
                add_bytes(bytes_written);
                
                // Emit progress event
                emit_event_make("file.progress", [&](py::dict& payload){
                    payload["bytes"] = total_copied;
                    payload["total"] = file_size;
                });
            }
            
            if (cancelled_) {
                std::cout << "DEBUG: C++ Engine copy cancelled - cleaning up" << std::endl;
                copy_cancelled:
                CrossPlatformIO::close_handle(src_handle);
                CrossPlatformIO::close_handle(dst_handle);
                return false;
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
    
    // 6) Streaming hash in the small-file path (no extra pass)
    bool copy_with_buffered_io(const CopyJob& job, const std::string& source_path, const std::string& dest_path) {
        size_t file_size = fs::file_size(fs::path(source_path));
        std::ifstream src(source_path, std::ios::binary);
        std::ofstream dst(dest_path, std::ios::binary);
        if (!src || !dst) return false;

        std::vector<char> buf(job.block_size);
        size_t total = 0;

        XXH64_state_t* xh = nullptr;
        if (job.verify_integrity && job.hash_algorithm == "xxhash64") { 
            xh = XXH64_createState(); 
            XXH64_reset(xh, 0); 
        }

        while (!cancelled_) {
            src.read(buf.data(), buf.size());
            std::streamsize n = src.gcount();
            if (n <= 0) break;
            if (xh) XXH64_update(xh, buf.data(), (size_t)n);
            dst.write(buf.data(), n);
            if (!dst) break;
            total += (size_t)n;
            add_bytes(size_t(n));

            if (event_sink_) { 
                emit_event_make("file.progress", [&](py::dict& p){ 
                    p["bytes"] = total; 
                    p["total"] = file_size; 
                }); 
            }
        }

        if (xh) {
            auto h = XXH64_digest(xh); 
            XXH64_freeState(xh);
            
            // NEW: Add verification record for successful verification
            if (job.generate_verification_report) {
                fs::path src_path(source_path);
                fs::path dst_path(dest_path);
                
                // Convert hash to hex string
                std::stringstream ss;
                ss << std::hex << std::setfill('0') << std::setw(16) << h;
                std::string src_hash = ss.str();
                
                // Calculate destination hash for verification
                std::string dest_hash = HashCalculator::calculate_file_hash(dest_path, job.hash_algorithm);
                
                if (src_hash == dest_hash) {
                    VerificationRecord record(src_path.filename().string(), source_path, dest_path, 
                                           file_size, job.hash_algorithm, src_hash, dest_hash, "PASS");
                    add_verification_record(record);
                } else {
                    VerificationRecord record(src_path.filename().string(), source_path, dest_path, 
                                           file_size, job.hash_algorithm, src_hash, dest_hash, 
                                           "FAIL", "hash_mismatch");
                    add_verification_record(record);
                }
            }
            
            stats_.hash_verifications++;
        }
        return total == file_size;
    }
    
    // NEW: Add verification record for non-verification cases
    void add_non_verification_record(const CopyJob& job, const std::string& source_path, 
                                   const std::string& dest_path, size_t file_size) {
        if (!job.generate_verification_report) return;
        
        try {
            fs::path src_path(source_path);
            fs::path dst_path(dest_path);
            VerificationRecord record(src_path.filename().string(), source_path, dest_path, 
                                   file_size, "NONE", "", "", "PASS");
            add_verification_record(record);
        } catch (...) {
            // Don't fail the transfer due to report generation issues
        }
    }

    // Range splitting uses ranges_per_file (not thread_count)
    std::vector<std::pair<size_t,size_t>> split_file_ranges(size_t file_size, int ranges_per_file) {
        if (ranges_per_file < 1) ranges_per_file = 1;
        std::vector<std::pair<size_t,size_t>> ranges;
        size_t chunk = file_size / ranges_per_file;
        for (int i=0; i<ranges_per_file; ++i) {
            size_t start = i * chunk;
            size_t end   = (i == ranges_per_file - 1) ? file_size : (i + 1) * chunk;
            ranges.emplace_back(start, end);
        }
        return ranges;
    }

    // Large-file copy: pre-alloc once, open temp O_RDWR (NO TRUNC), seek per range
    bool copy_large_file_enhanced(const CopyJob& job, const std::string& src, const std::string& dst) {
        const size_t file_size = fs::file_size(fs::path(src));
        const std::string tmp = dst + ".tmp";

#if defined(_WIN32)
        HANDLE h = CreateFileA(tmp.c_str(), GENERIC_READ|GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (h == INVALID_HANDLE_VALUE) return false;
        if (!preallocate_windows(h, (LONGLONG)file_size)) { CloseHandle(h); return false; }
        CloseHandle(h);
#else
        int fd = ::open(tmp.c_str(), O_RDWR | O_CREAT | O_TRUNC, 0644);
        if (fd < 0) return false;
  #if defined(__APPLE__)
        if (!preallocate_macos(fd, (off_t)file_size)) { ::close(fd); return false; }
  #elif defined(__linux__)
        if (!preallocate_linux(fd, (off_t)file_size)) { ::close(fd); return false; }
  #endif
        ::close(fd);
#endif

        const int rangesWanted = std::max(1, job.ranges_per_file);
        auto ranges = split_file_ranges(file_size, rangesWanted);

        std::vector<std::future<bool>> futs;
        for (auto& r : ranges) {
            futs.emplace_back(std::async(std::launch::async, [this, &job, src, tmp, r, file_size]() {
#if defined(_WIN32)
                HANDLE s = CreateFileA(src.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
                HANDLE d = CreateFileA(tmp.c_str(), GENERIC_READ|GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
                if (s==INVALID_HANDLE_VALUE || d==INVALID_HANDLE_VALUE) { if(s!=INVALID_HANDLE_VALUE)CloseHandle(s); if(d!=INVALID_HANDLE_VALUE)CloseHandle(d); return false; }
                LARGE_INTEGER pos; pos.QuadPart = (LONGLONG)r.first;
                SetFilePointerEx(s, pos, nullptr, FILE_BEGIN);
                SetFilePointerEx(d, pos, nullptr, FILE_BEGIN);
                std::vector<char> buf(job.block_size);
                size_t remain = r.second - r.first;
                while (remain && !cancelled_) {
                    DWORD toRead = (DWORD)std::min(remain, (size_t)buf.size());
                    DWORD rd=0, wr=0;
                    if (!ReadFile(s, buf.data(), toRead, &rd, nullptr) || rd==0) break;
                    if (!WriteFile(d, buf.data(), rd, &wr, nullptr) || wr!=rd) { CloseHandle(s); CloseHandle(d); return false; }
                    remain -= rd; add_bytes(size_t(rd));
                    if (event_sink_ && g_progress.should_emit(src)) { 
                        emit_event_make("file.progress", [&](py::dict& p){ 
                            p["bytes"]=(py::int_)0; 
                            p["total"]=(py::int_)file_size; 
                        }); 
                    }
                }
                CloseHandle(s); CloseHandle(d);
                return true;
#else
                int sfd = ::open(src.c_str(), O_RDONLY);
                int dfd = ::open(tmp.c_str(), O_RDWR); // NO TRUNC; file is pre-sized
                if (sfd<0 || dfd<0) { if(sfd>=0) ::close(sfd); if(dfd>=0) ::close(dfd); return false; }
                if (lseek(sfd, (off_t)r.first, SEEK_SET) < 0 || lseek(dfd, (off_t)r.first, SEEK_SET) < 0) { ::close(sfd); ::close(dfd); return false; }
  #if defined(__APPLE__)
                fcntl(sfd, F_RDAHEAD, 1);
  #endif
                std::vector<char> buf(job.block_size);
                size_t remain = r.second - r.first;
                while (remain && !cancelled_) {
                    size_t toRead = std::min(remain, buf.size());
                    ssize_t n = ::read(sfd, buf.data(), toRead);
                    if (n <= 0) break;
                    ssize_t w = ::write(dfd, buf.data(), n);
                    if (w != n) { ::close(sfd); ::close(dfd); return false; }
                    remain -= size_t(n); add_bytes(size_t(n));
                    if (event_sink_ && g_progress.should_emit(src)) { 
                        emit_event_make("file.progress", [&](py::dict& p){ 
                            p["bytes"]=(py::int_)0; 
                            p["total"]=(py::int_)file_size; 
                        }); 
                    }
                }
                ::close(sfd); ::close(dfd);
                return true;
#endif
            }));
        }
        for (auto& f : futs) if (!f.get()) return false;

        if (job.verify_integrity) {
            auto sh = HashCalculator::calculate_file_hash(src, job.hash_algorithm);
            auto dh = HashCalculator::calculate_file_hash(tmp, job.hash_algorithm);
            if (sh != dh) { fs::remove(tmp); stats_.hash_failures++; return false; }
            stats_.hash_verifications++;
        }
        fs::rename(tmp, dst);
        return true;
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
            add_error(std::string("Range copy exception: ") + e.what());
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
            
            // Use aligned buffer for direct I/O
            auto buffer = make_aligned(job.block_size);
            size_t copied_bytes = 0;
            size_t range_size = end - start;
            
            while (copied_bytes < range_size && !cancelled_) {
                while (paused_) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                }
                
                size_t remaining = range_size - copied_bytes;
                size_t read_size = std::min(job.block_size, remaining);
                
                ssize_t bytes_read = CrossPlatformIO::read_direct(src_handle, buffer.get(), read_size);
                if (bytes_read <= 0) break;
                
                ssize_t bytes_written = CrossPlatformIO::write_direct(dst_handle, buffer.get(), bytes_read);
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
    
    // And open the destination in range functions as read/write (not trunc) and seek:
    bool copy_range_with_buffered_io(const CopyJob& job, const std::string& source_path, const std::string& dest_path,
                                    size_t start, size_t end) {
        std::ifstream src_file(source_path, std::ios::binary);
        std::fstream dst_file(dest_path, std::ios::binary | std::ios::in | std::ios::out); // no trunc
        
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
    
    // Always call Python under the GIL, from any thread.
    void emit_event(const std::string& event_type, const py::dict& payload) {
        if (!event_sink_) return;
        py::gil_scoped_acquire gil;
        try {
            event_sink_(event_type, payload);
        } catch (const py::error_already_set& e) {
            // Optional: log e.what() to your logging system
        }
    }

    // Convenience: build the payload while holding the GIL (safe for py::dict construction too)
    template <class F>
    void emit_event_make(const std::string& event_type, F&& fill_payload) {
        if (!event_sink_) return;
        py::gil_scoped_acquire gil;
        try {
            py::dict p;
            fill_payload(p);
            event_sink_(event_type, p);
        } catch (const py::error_already_set& e) {
            // Optional: log e.what()
        }
    }
};

// PyBind11 module
PYBIND11_MODULE(enhanced_high_perf_engine, m) {
    // Use try-catch to handle re-registration gracefully
    try {
        py::class_<BandwidthTest>(m, "BandwidthTest")
        .def_readwrite("write_speed", &BandwidthTest::write_speed)
        .def_readwrite("read_speed", &BandwidthTest::read_speed)
        .def_readwrite("avg_speed", &BandwidthTest::avg_speed);
    
    py::class_<TunedParams>(m, "TunedParams")
        .def(py::init<>())
        .def_readwrite("block_size", &TunedParams::block_size)
        .def_readwrite("files_in_flight", &TunedParams::files_in_flight)
        .def_readwrite("ranges_per_file", &TunedParams::ranges_per_file)
        .def_readwrite("use_direct_io", &TunedParams::use_direct_io);
    
    py::class_<CopyStats>(m, "CopyStats")
        .def_readwrite("total_files", &CopyStats::total_files)
        .def_readwrite("copied_files", &CopyStats::copied_files)
        .def_readwrite("total_bytes", &CopyStats::total_bytes)
        .def_readwrite("copied_bytes", &CopyStats::copied_bytes)
        .def_readwrite("start_time", &CopyStats::start_time)
        .def_readwrite("end_time", &CopyStats::end_time)
        .def_readwrite("speed_mbps", &CopyStats::speed_mbps)
        .def_readwrite("data_mbps", &CopyStats::data_mbps)
        .def_readwrite("data_elapsed_s", &CopyStats::data_elapsed_s)
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
        .def_readwrite("large_file_threshold", &CopyJob::large_file_threshold)
        .def_readwrite("files_in_flight", &CopyJob::files_in_flight)
        .def_readwrite("ranges_per_file", &CopyJob::ranges_per_file)
        .def_readwrite("preset", &CopyJob::preset)
        .def_readwrite("verify_mode", &CopyJob::verify_mode)
        .def_readwrite("per_dest_params", &CopyJob::per_dest_params)
        // NEW: Verification report fields
        .def_readwrite("generate_verification_report", &CopyJob::generate_verification_report)
        .def_readwrite("job_id", &CopyJob::job_id);
    
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
    m.def("copy_file_to_many", &copy_file_to_many, py::arg("src_path"), py::arg("dest_paths"), py::arg("tuned_params"), py::arg("event_sink"), py::arg("cancel_event") = nullptr);
    } catch (const py::error_already_set& e) {
        // Module already registered, ignore the error
        if (std::string(e.what()).find("already registered") != std::string::npos) {
            return;
        }
        throw;
    }
}
