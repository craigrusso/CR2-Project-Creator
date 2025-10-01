//! Python bindings for ForwardFlow V2.0 Rust engine components
//!
//! High-performance, zero-copy Python bindings for the Rust engine core,
//! EventHub, TransferStrategyEngine, and BLAST engine. Designed for minimal
//! overhead and maximum performance in professional DIT workflows.

use anyhow::Result;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::path::PathBuf;
use std::sync::Arc;

use crate::blast_engine::{BlastConfig, BlastEngine, BlastTransferResult};
use crate::event_hub_v2::{
    EventHub, EventHubStats, EventPayload, EventPriority, EventType, TransferEvent,
};
use crate::strategy_engine::{DestinationAnalysis, TransferStrategy, TransferStrategyEngine};

/// Python wrapper for the high-performance EventHub
#[pyclass(name = "EventHubV2")]
pub struct PyEventHubV2 {
    inner: Arc<EventHub>,
}

#[pymethods]
impl PyEventHubV2 {
    #[new]
    fn new() -> PyResult<Self> {
        match EventHub::new() {
            Ok(hub) => Ok(Self {
                inner: Arc::new(hub),
            }),
            Err(e) => Err(PyRuntimeError::new_err(format!(
                "Failed to create EventHub: {}",
                e
            ))),
        }
    }

    /// Emit a transfer event to the hub
    fn emit_event(&self, py: Python, event_data: &PyDict) -> PyResult<()> {
        let event = self.dict_to_transfer_event(py, event_data)?;

        self.inner
            .emit_event(event)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to emit event: {}", e)))
    }

    /// Get comprehensive performance statistics
    fn get_stats(&self, py: Python) -> PyResult<PyObject> {
        let stats = self.inner.get_stats();
        self.stats_to_dict(py, &stats)
    }

    /// Shutdown the event hub gracefully
    fn shutdown(&mut self) -> PyResult<()> {
        // Note: Can't call shutdown on Arc<EventHub> directly
        // In practice, the EventHub will shutdown when dropped
        Ok(())
    }
}

impl PyEventHubV2 {
    /// Get a reference to the inner EventHub for other Rust components
    pub fn get_inner(&self) -> Arc<EventHub> {
        self.inner.clone()
    }

    fn get_string_item(data: &PyDict, key: &str, default: &str) -> PyResult<String> {
        match data.get_item(key) {
            Ok(Some(value)) => value.extract().or_else(|_| Ok(default.to_string())),
            _ => Ok(default.to_string()),
        }
    }

    fn get_u64_item(data: &PyDict, key: &str, default: u64) -> PyResult<u64> {
        match data.get_item(key) {
            Ok(Some(value)) => value.extract().or_else(|_| Ok(default)),
            _ => Ok(default),
        }
    }

    fn get_f64_item(data: &PyDict, key: &str, default: f64) -> PyResult<f64> {
        match data.get_item(key) {
            Ok(Some(value)) => value.extract().or_else(|_| Ok(default)),
            _ => Ok(default),
        }
    }

    fn get_optional_string(data: &PyDict, key: &str) -> PyResult<Option<String>> {
        match data.get_item(key) {
            Ok(Some(value)) => Ok(Some(value.extract().unwrap_or_default())),
            _ => Ok(None),
        }
    }

    /// Convert Python dict to TransferEvent
    fn dict_to_transfer_event(&self, _py: Python, data: &PyDict) -> PyResult<TransferEvent> {
        let event_type_str = Self::get_string_item(data, "event_type", "FileProgress")?;
        let priority_str = Self::get_string_item(data, "priority", "Normal")?;
        let job_id = Self::get_string_item(data, "job_id", "unknown")?;

        let event_type = match event_type_str.as_str() {
            "FileStarted" => EventType::FileStarted,
            "FileProgress" => EventType::FileProgress,
            "FileCompleted" => EventType::FileCompleted,
            "FileError" => EventType::FileError,
            "DestStarted" => EventType::DestStarted,
            "DestProgress" => EventType::DestProgress,
            "DestCompleted" => EventType::DestCompleted,
            "DestError" => EventType::DestError,
            "JobStarted" => EventType::JobStarted,
            "JobProgress" => EventType::JobProgress,
            "JobCompleted" => EventType::JobCompleted,
            "JobError" => EventType::JobError,
            "BlastInitiated" => EventType::BlastInitiated,
            "BlastCompleted" => EventType::BlastCompleted,
            _ => {
                return Err(PyValueError::new_err(format!(
                    "Unknown event type: {}",
                    event_type_str
                )))
            }
        };

        let priority = match priority_str.as_str() {
            "Critical" => EventPriority::Critical,
            "High" => EventPriority::High,
            "Normal" => EventPriority::Normal,
            "Low" => EventPriority::Low,
            _ => EventPriority::Normal,
        };

        // Extract payload based on event type
        let payload = match data.get_item("payload") {
            Ok(Some(payload_value)) => {
                let payload_dict = payload_value.downcast::<PyDict>()?;
                self.dict_to_event_payload(_py, payload_dict)?
            }
            _ => {
                // Default payload
                EventPayload::System {
                    message: "Default event".to_string(),
                    data: serde_json::Value::Null,
                }
            }
        };

        Ok(TransferEvent::new(event_type, priority, job_id, payload))
    }

    /// Convert Python dict to EventPayload
    fn dict_to_event_payload(&self, _py: Python, data: &PyDict) -> PyResult<EventPayload> {
        let payload_type = Self::get_string_item(data, "type", "System")?;

        match payload_type.as_str() {
            "File" => Ok(EventPayload::File {
                file_id: Self::get_string_item(data, "file_id", "")?,
                filename: Self::get_string_item(data, "filename", "")?,
                file_size: Self::get_u64_item(data, "file_size", 0)?,
                bytes_copied: Self::get_u64_item(data, "bytes_copied", 0)?,
                destination_path: Self::get_string_item(data, "destination_path", "")?,
                source_checksum: Self::get_optional_string(data, "source_checksum")?,
                destination_checksum: Self::get_optional_string(data, "destination_checksum")?,
                hash_algorithm: Self::get_string_item(data, "hash_algorithm", "xxHash64BE")?,
                transfer_speed_mbps: Self::get_f64_item(data, "transfer_speed_mbps", 0.0)?,
                error_message: Self::get_optional_string(data, "error_message")?,
            }),
            "Job" => Ok(EventPayload::Job {
                total_destinations: Self::get_u64_item(data, "total_destinations", 0)? as usize,
                completed_destinations: Self::get_u64_item(data, "completed_destinations", 0)?
                    as usize,
                total_speed_mbps: Self::get_f64_item(data, "total_speed_mbps", 0.0)?,
                peak_speed_mbps: Self::get_f64_item(data, "peak_speed_mbps", 0.0)?,
                progress_percent: Self::get_f64_item(data, "progress_percent", 0.0)?,
                eta_seconds: Self::get_f64_item(data, "eta_seconds", 0.0)?,
                total_bytes: Self::get_u64_item(data, "total_bytes", 0)?,
                copied_bytes: Self::get_u64_item(data, "copied_bytes", 0)?,
                total_files: Self::get_u64_item(data, "total_files", 0)? as usize,
                completed_files: Self::get_u64_item(data, "completed_files", 0)? as usize,
                strategy_name: Self::get_string_item(data, "strategy_name", "Unknown")?,
                error_message: Self::get_optional_string(data, "error_message")?,
            }),
            _ => Ok(EventPayload::System {
                message: Self::get_string_item(data, "message", "System event")?,
                data: serde_json::Value::Null,
            }),
        }
    }

    /// Convert EventHubStats to Python dict
    fn stats_to_dict(&self, py: Python, stats: &EventHubStats) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("events_processed", stats.events_processed)?;
        dict.set_item("events_dropped", stats.events_dropped)?;
        dict.set_item("avg_processing_time_ns", stats.avg_processing_time_ns)?;
        dict.set_item("peak_processing_time_ns", stats.peak_processing_time_ns)?;
        dict.set_item("active_threads", stats.active_threads)?;

        // Convert events_by_type
        let events_by_type = PyDict::new(py);
        for (event_type, count) in &stats.events_by_type {
            let type_str = format!("{:?}", event_type);
            events_by_type.set_item(type_str, *count)?;
        }
        dict.set_item("events_by_type", events_by_type)?;

        Ok(dict.into())
    }
}

/// Python wrapper for the TransferStrategyEngine
#[pyclass(name = "TransferStrategyEngine")]
pub struct PyTransferStrategyEngine {
    inner: TransferStrategyEngine,
}

#[pymethods]
impl PyTransferStrategyEngine {
    #[new]
    fn new(event_hub: Option<&PyEventHubV2>) -> Self {
        let inner = if let Some(hub) = event_hub {
            TransferStrategyEngine::with_event_hub(hub.get_inner())
        } else {
            TransferStrategyEngine::new()
        };

        Self { inner }
    }

    /// Analyze destinations and select optimal transfer strategy
    #[pyo3(signature = (destinations, total_bytes, blast_cache=None, job_id=""))]
    fn analyze_and_select_strategy(
        &self,
        py: Python,
        destinations: &PyList,
        total_bytes: u64,
        blast_cache: Option<&str>,
        job_id: &str,
    ) -> PyResult<PyObject> {
        // Convert Python list to PathBuf vector
        let dest_paths: PyResult<Vec<PathBuf>> = destinations
            .iter()
            .map(|item| {
                let path_str: String = item.extract()?;
                Ok(PathBuf::from(path_str))
            })
            .collect();

        let dest_paths = dest_paths?;
        let blast_cache_path = blast_cache.map(PathBuf::from);

        // Call Rust implementation
        let result = self.inner.analyze_and_select_strategy(
            &dest_paths,
            total_bytes,
            blast_cache_path,
            job_id,
        );

        match result {
            Ok((strategy, analyses)) => {
                let result_dict = PyDict::new(py);
                result_dict.set_item("strategy", self.strategy_to_dict(py, &strategy)?)?;
                result_dict.set_item("analyses", self.analyses_to_list(py, &analyses)?)?;
                Ok(result_dict.into())
            }
            Err(e) => Err(PyRuntimeError::new_err(format!(
                "Strategy analysis failed: {}",
                e
            ))),
        }
    }

    /// Analyze a single destination
    fn analyze_destination(&self, py: Python, destination: &str) -> PyResult<PyObject> {
        let dest_path = PathBuf::from(destination);

        match self.inner.analyze_destination(&dest_path) {
            Ok(analysis) => self.analysis_to_dict(py, &analysis),
            Err(e) => Err(PyRuntimeError::new_err(format!(
                "Destination analysis failed: {}",
                e
            ))),
        }
    }
}

impl PyTransferStrategyEngine {
    /// Convert TransferStrategy to Python dict
    fn strategy_to_dict(&self, py: Python, strategy: &TransferStrategy) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("name", strategy.name())?;

        match strategy {
            TransferStrategy::DirectCopy {
                destination,
                use_memory_mapping,
                chunk_size_mb,
            } => {
                dict.set_item("type", "DirectCopy")?;
                dict.set_item("destination", destination.to_string_lossy().as_ref())?;
                dict.set_item("use_memory_mapping", *use_memory_mapping)?;
                dict.set_item("chunk_size_mb", *chunk_size_mb)?;
            }
            TransferStrategy::MemoryStaging {
                destinations,
                buffer_size_mb,
                parallel_writes,
            } => {
                dict.set_item("type", "MemoryStaging")?;
                let dest_list = PyList::new(
                    py,
                    destinations.iter().map(|p| p.to_string_lossy().to_string()),
                );
                dict.set_item("destinations", dest_list)?;
                dict.set_item("buffer_size_mb", *buffer_size_mb)?;
                dict.set_item("parallel_writes", *parallel_writes)?;
            }
            TransferStrategy::GpuAccelerated {
                gpu_staging,
                final_destinations,
                compute_pipeline,
                use_unified_memory,
            } => {
                dict.set_item("type", "GpuAccelerated")?;
                dict.set_item("gpu_staging", gpu_staging.to_string_lossy().as_ref())?;
                let dest_list = PyList::new(
                    py,
                    final_destinations
                        .iter()
                        .map(|p| p.to_string_lossy().to_string()),
                );
                dict.set_item("final_destinations", dest_list)?;
                dict.set_item("compute_pipeline", format!("{:?}", compute_pipeline))?;
                dict.set_item("use_unified_memory", *use_unified_memory)?;
            }
            TransferStrategy::BlastWorkflow {
                blast_cache,
                final_destinations,
                ..
            } => {
                dict.set_item("type", "BlastWorkflow")?;
                dict.set_item("blast_cache", blast_cache.to_string_lossy().as_ref())?;
                let dest_list = PyList::new(
                    py,
                    final_destinations
                        .iter()
                        .map(|p| p.to_string_lossy().to_string()),
                );
                dict.set_item("final_destinations", dest_list)?;
            }
            TransferStrategy::HybridMultiStrategy { strategies } => {
                dict.set_item("type", "HybridMultiStrategy")?;
                dict.set_item("strategy_count", strategies.len())?;
            }
        }

        Ok(dict.into())
    }

    /// Convert DestinationAnalysis to Python dict
    fn analysis_to_dict(&self, py: Python, analysis: &DestinationAnalysis) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("path", analysis.path.to_string_lossy().as_ref())?;
        dict.set_item("dest_type", format!("{:?}", analysis.dest_type))?;
        dict.set_item("available_space_bytes", analysis.available_space_bytes)?;
        dict.set_item("benchmarked_speed_mbps", analysis.benchmarked_speed_mbps)?;
        dict.set_item("optimal_chunk_size_mb", analysis.optimal_chunk_size_mb)?;
        dict.set_item("supports_direct_io", analysis.supports_direct_io)?;
        dict.set_item("is_network_path", analysis.is_network_path)?;

        // Volume info
        let volume_dict = PyDict::new(py);
        volume_dict.set_item("filesystem", &analysis.volume_info.filesystem)?;
        volume_dict.set_item(
            "mount_point",
            analysis.volume_info.mount_point.to_string_lossy().as_ref(),
        )?;
        volume_dict.set_item("is_case_sensitive", analysis.volume_info.is_case_sensitive)?;
        volume_dict.set_item(
            "supports_sparse_files",
            analysis.volume_info.supports_sparse_files,
        )?;
        volume_dict.set_item("block_size", analysis.volume_info.block_size)?;
        dict.set_item("volume_info", volume_dict)?;

        // GPU info (if available)
        if let Some(ref gpu_info) = analysis.gpu_info {
            let gpu_dict = PyDict::new(py);
            gpu_dict.set_item("device_name", &gpu_info.device_name)?;
            gpu_dict.set_item("memory_gb", gpu_info.memory_gb)?;
            gpu_dict.set_item("compute_units", gpu_info.compute_units)?;
            gpu_dict.set_item("memory_bandwidth_gbps", gpu_info.memory_bandwidth_gbps)?;
            gpu_dict.set_item("supports_unified_memory", gpu_info.supports_unified_memory)?;
            dict.set_item("gpu_info", gpu_dict)?;
        }

        Ok(dict.into())
    }

    /// Convert analyses vector to Python list
    fn analyses_to_list(&self, py: Python, analyses: &[DestinationAnalysis]) -> PyResult<PyObject> {
        let list = PyList::empty(py);
        for analysis in analyses {
            list.append(self.analysis_to_dict(py, analysis)?)?;
        }
        Ok(list.into())
    }
}

/// Python wrapper for the BLAST engine
#[pyclass(name = "BlastEngine")]
pub struct PyBlastEngine {
    inner: BlastEngine,
}

#[pymethods]
impl PyBlastEngine {
    #[new]
    fn new(py: Python, config_dict: &PyDict, event_hub: Option<&PyEventHubV2>) -> PyResult<Self> {
        let config = Self::dict_to_blast_config(py, config_dict)?;

        let inner = if let Some(hub) = event_hub {
            BlastEngine::with_event_hub(config, hub.get_inner())
        } else {
            BlastEngine::new(config)
        };

        Ok(Self { inner })
    }

    /// Execute complete BLAST workflow (placeholder for now)
    fn execute_blast_transfer(
        &self,
        py: Python,
        source_files: &PyList,
        job_id: &str,
    ) -> PyResult<PyObject> {
        // Placeholder implementation - will be completed when BlastEngine is fully implemented
        let dict = PyDict::new(py);
        dict.set_item("status", "not_implemented")?;
        dict.set_item("message", "BLAST engine not yet fully implemented")?;
        Ok(dict.into())
    }

    /// Cancel ongoing BLAST operation
    fn cancel(&self) {
        self.inner.cancel();
    }
}

impl PyBlastEngine {
    /// Convert Python dict to BlastConfig
    fn dict_to_blast_config(_py: Python, data: &PyDict) -> PyResult<BlastConfig> {
        let mut config = BlastConfig::default();

        if let Ok(Some(cache_path)) = data.get_item("blast_cache_path") {
            config.blast_cache_path = PathBuf::from(cache_path.extract::<String>()?);
        }

        if let Ok(Some(targets)) = data.get_item("distribution_targets") {
            let targets_list: &PyList = targets.downcast()?;
            config.distribution_targets = targets_list
                .iter()
                .map(|item| PathBuf::from(item.extract::<String>().unwrap()))
                .collect();
        }

        if let Ok(Some(buffer_mb)) = data.get_item("memory_buffer_mb") {
            config.memory_buffer_mb = buffer_mb.extract()?;
        }

        if let Ok(Some(streams)) = data.get_item("max_parallel_streams") {
            config.max_parallel_streams = streams.extract()?;
        }

        if let Ok(Some(direct_io)) = data.get_item("use_direct_io") {
            config.use_direct_io = direct_io.extract()?;
        }

        if let Ok(Some(mmap)) = data.get_item("use_memory_mapping") {
            config.use_memory_mapping = mmap.extract()?;
        }

        if let Ok(Some(chunk_size)) = data.get_item("cache_chunk_size_mb") {
            config.cache_chunk_size_mb = chunk_size.extract()?;
        }

        Ok(config)
    }

    /// Convert BlastTransferResult to Python dict (static version for async)
    fn blast_result_to_dict_static(py: Python, result: &BlastTransferResult) -> PyResult<PyObject> {
        Self::blast_result_to_dict_impl(py, result)
    }

    /// Convert BlastTransferResult to Python dict
    fn blast_result_to_dict(&self, py: Python, result: &BlastTransferResult) -> PyResult<PyObject> {
        Self::blast_result_to_dict_impl(py, result)
    }

    /// Implementation for converting BlastTransferResult to Python dict
    fn blast_result_to_dict_impl(py: Python, result: &BlastTransferResult) -> PyResult<PyObject> {
        let dict = PyDict::new(py);

        // Cache result
        let cache_dict = PyDict::new(py);
        cache_dict.set_item("files_cached", result.cache_result.files_cached)?;
        cache_dict.set_item("bytes_cached", result.cache_result.bytes_cached)?;
        cache_dict.set_item(
            "duration_seconds",
            result.cache_result.duration.as_secs_f64(),
        )?;
        cache_dict.set_item("average_speed_mbps", result.cache_result.average_speed_mbps)?;
        dict.set_item("cache_result", cache_dict)?;

        // Distribution result
        let dist_dict = PyDict::new(py);
        dist_dict.set_item(
            "files_distributed",
            result.distribution_result.files_distributed,
        )?;
        dist_dict.set_item(
            "bytes_distributed",
            result.distribution_result.bytes_distributed,
        )?;
        dist_dict.set_item(
            "duration_seconds",
            result.distribution_result.duration.as_secs_f64(),
        )?;
        dist_dict.set_item(
            "average_speed_mbps",
            result.distribution_result.average_speed_mbps,
        )?;
        dict.set_item("distribution_result", dist_dict)?;

        // Verification result
        let verify_dict = PyDict::new(py);
        verify_dict.set_item("files_verified", result.verification_result.files_verified)?;
        verify_dict.set_item(
            "verification_passed",
            result.verification_result.verification_passed,
        )?;
        verify_dict.set_item(
            "failed_files",
            result.verification_result.failed_files.len(),
        )?;
        dict.set_item("verification_result", verify_dict)?;

        // Overall stats
        dict.set_item("total_time_seconds", result.total_time.as_secs_f64())?;

        Ok(dict.into())
    }
}

/// Register all Python types for this module
pub fn register_python_types(m: &PyModule) -> PyResult<()> {
    m.add_class::<PyEventHubV2>()?;
    m.add_class::<PyTransferStrategyEngine>()?;
    m.add_class::<PyBlastEngine>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_python_bindings_creation() {
        // Test that Python bindings can be created without panicking
        Python::with_gil(|py| {
            let hub = PyEventHubV2::new();
            assert!(hub.is_ok());

            let strategy_engine = PyTransferStrategyEngine::new(None);
            // Should not panic
        });
    }
}
