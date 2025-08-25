#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <string>
#include <vector>
#include <functional>
#include <chrono>
#include <thread>
#include <atomic>

// Include the real engine implementation
#include "core/engine_core.hpp"
#include "core/data_structures.hpp"

namespace py = pybind11;

// PyBind11 module
PYBIND11_MODULE(enhanced_high_perf_engine, m) {
    // Expose CopyJob using the real engine's data structures
    // Also expose TunedParams so Python can pass per-destination tuning to the C++ engine
    py::class_<DataStructures::TunedParams>(m, "TunedParams")
        .def(py::init<>())
        .def_readwrite("block_size", &DataStructures::TunedParams::block_size)
        .def_readwrite("files_in_flight", &DataStructures::TunedParams::files_in_flight)
        .def_readwrite("ranges_per_file", &DataStructures::TunedParams::ranges_per_file)
        .def_readwrite("use_direct_io", &DataStructures::TunedParams::use_direct_io);
    
    // Expose DestProgressPayload for proper Python access
    py::class_<DataStructures::DestProgressPayload>(m, "DestProgressPayload")
        .def(py::init<>())
        .def_readwrite("dest_index", &DataStructures::DestProgressPayload::dest_index)
        .def_readwrite("dest_path", &DataStructures::DestProgressPayload::dest_path)
        .def_readwrite("transfer_type", &DataStructures::DestProgressPayload::transfer_type)
        .def_readwrite("bytes_copied", &DataStructures::DestProgressPayload::bytes_copied)
        .def_readwrite("total_bytes", &DataStructures::DestProgressPayload::total_bytes)
        .def_readwrite("current_speed_mbps", &DataStructures::DestProgressPayload::current_speed_mbps)
        .def_readwrite("peak_speed_mbps", &DataStructures::DestProgressPayload::peak_speed_mbps)
        .def_readwrite("elapsed_time", &DataStructures::DestProgressPayload::elapsed_time)
        .def_readwrite("completed_files", &DataStructures::DestProgressPayload::completed_files)
        .def_readwrite("total_files", &DataStructures::DestProgressPayload::total_files);

    py::class_<DataStructures::CopyJob>(m, "CopyJob")
        .def(py::init<>())
        .def_readwrite("source_paths", &DataStructures::CopyJob::source_paths)
        .def_readwrite("destination_paths", &DataStructures::CopyJob::destination_paths)
        .def_readwrite("block_size", &DataStructures::CopyJob::block_size)
        .def_readwrite("thread_count", &DataStructures::CopyJob::thread_count)
        .def_readwrite("use_direct_io", &DataStructures::CopyJob::use_direct_io)
        .def_readwrite("verify_integrity", &DataStructures::CopyJob::verify_integrity)
        .def_readwrite("hash_algorithm", &DataStructures::CopyJob::hash_algorithm)
        .def_readwrite("mtu_size", &DataStructures::CopyJob::mtu_size)
        .def_readwrite("socket_buffer_size", &DataStructures::CopyJob::socket_buffer_size)
        .def_readwrite("adaptive_parameters", &DataStructures::CopyJob::adaptive_parameters)
        .def_readwrite("large_file_threshold", &DataStructures::CopyJob::large_file_threshold)
        .def_readwrite("files_in_flight", &DataStructures::CopyJob::files_in_flight)
        .def_readwrite("ranges_per_file", &DataStructures::CopyJob::ranges_per_file)
        .def_readwrite("preset", &DataStructures::CopyJob::preset)
        .def_readwrite("verify_mode", &DataStructures::CopyJob::verify_mode)
        .def_readwrite("per_dest_params", &DataStructures::CopyJob::per_dest_params)
        .def_readwrite("generate_verification_report", &DataStructures::CopyJob::generate_verification_report)
        .def_readwrite("job_id", &DataStructures::CopyJob::job_id)
        .def_readwrite("reports_folder_name", &DataStructures::CopyJob::reports_folder_name)
        .def_readwrite("cloud_source", &DataStructures::CopyJob::cloud_source);

    // Expose CopyStats using the real engine's data structures
    py::class_<DataStructures::CopyStats>(m, "CopyStats")
        .def(py::init<>())
        .def_readwrite("total_files", &DataStructures::CopyStats::total_files)
        .def_readwrite("copied_files", &DataStructures::CopyStats::copied_files)
        .def_readwrite("total_bytes", &DataStructures::CopyStats::total_bytes)
        .def_readwrite("copied_bytes", &DataStructures::CopyStats::copied_bytes)
        .def_readwrite("start_time", &DataStructures::CopyStats::start_time)
        .def_readwrite("end_time", &DataStructures::CopyStats::end_time)
        .def_readwrite("speed_mbps", &DataStructures::CopyStats::speed_mbps)
        .def_readwrite("data_mbps", &DataStructures::CopyStats::data_mbps)
        .def_readwrite("data_elapsed_s", &DataStructures::CopyStats::data_elapsed_s)
        .def_readwrite("errors", &DataStructures::CopyStats::errors)
        .def_readwrite("hash_verifications", &DataStructures::CopyStats::hash_verifications)
        .def_readwrite("hash_failures", &DataStructures::CopyStats::hash_failures)
        .def("duration", &DataStructures::CopyStats::duration)
        .def("success_rate", &DataStructures::CopyStats::success_rate);

    // Expose the real EnhancedHighPerfTransferEngine
    py::class_<EngineCore::EnhancedHighPerfTransferEngine>(m, "EnhancedHighPerfTransferEngine")
        .def(py::init<>())
        .def("set_event_sink", &EngineCore::EnhancedHighPerfTransferEngine::set_event_sink)
        .def("copy_files", &EngineCore::EnhancedHighPerfTransferEngine::copy_files)
        .def("cancel", &EngineCore::EnhancedHighPerfTransferEngine::cancel)
        .def("pause", &EngineCore::EnhancedHighPerfTransferEngine::pause)
        .def("resume", &EngineCore::EnhancedHighPerfTransferEngine::resume)
        .def("write_verification_reports", &EngineCore::EnhancedHighPerfTransferEngine::write_verification_reports)
        .def("write_verification_reports_to_destination", &EngineCore::EnhancedHighPerfTransferEngine::write_verification_reports_to_destination)
        .def("emit_dest_progress", &EngineCore::EnhancedHighPerfTransferEngine::emit_dest_progress)
        .def("emit_job_progress", &EngineCore::EnhancedHighPerfTransferEngine::emit_job_progress)
        .def("emit_file_completed", &EngineCore::EnhancedHighPerfTransferEngine::emit_file_completed);
}
