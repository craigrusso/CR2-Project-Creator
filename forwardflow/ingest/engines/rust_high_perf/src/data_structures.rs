//! Data structures for the high-performance transfer engine

use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Copy destination with tuning parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct CopyDestination {
    #[pyo3(get, set)]
    pub path: String,
    #[pyo3(get, set)]
    pub block_size: Option<usize>,
    #[pyo3(get, set)]
    pub files_in_flight: Option<usize>,
    #[pyo3(get, set)]
    pub use_direct_io: Option<bool>,
}

impl Default for CopyDestination {
    fn default() -> Self {
        Self {
            path: String::new(),
            block_size: Some(4 * 1024 * 1024), // 4MB default
            files_in_flight: Some(4),
            use_direct_io: Some(false),
        }
    }
}

/// Tuned parameters for each destination
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct TunedParams {
    #[pyo3(get, set)]
    pub block_size: usize,
    #[pyo3(get, set)]
    pub files_in_flight: usize,
    #[pyo3(get, set)]
    pub ranges_per_file: usize,
    #[pyo3(get, set)]
    pub use_direct_io: bool,
}

impl Default for TunedParams {
    fn default() -> Self {
        Self {
            block_size: 4 * 1024 * 1024, // 4 MB default
            files_in_flight: 1,
            ranges_per_file: 1,
            use_direct_io: false,
        }
    }
}

/// Copy statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct CopyStats {
    #[pyo3(get, set)]
    pub total_files: usize,
    #[pyo3(get, set)]
    pub copied_files: usize,
    #[pyo3(get, set)]
    pub total_bytes: u64,
    #[pyo3(get, set)]
    pub copied_bytes: u64,
    #[pyo3(get, set)]
    pub start_time: f64,
    #[pyo3(get, set)]
    pub end_time: f64,
    #[pyo3(get, set)]
    pub speed_mib_s: f64,
    #[pyo3(get, set)]
    pub data_mib_s: f64,
    #[pyo3(get, set)]
    pub data_elapsed_s: f64,
    #[pyo3(get, set)]
    pub errors: Vec<String>,
    #[pyo3(get, set)]
    pub hash_verifications: usize,
    #[pyo3(get, set)]
    pub hash_failures: usize,
    #[pyo3(get, set)]
    pub files: Vec<FileTransferRecord>,
}

impl CopyStats {
    pub fn duration(&self) -> f64 {
        self.end_time - self.start_time
    }
    
    pub fn success_rate(&self) -> f64 {
        if self.total_files > 0 {
            (self.copied_files as f64 * 100.0) / self.total_files as f64
        } else {
            0.0
        }
    }
}

impl Default for CopyStats {
    fn default() -> Self {
        Self {
            total_files: 0,
            copied_files: 0,
            total_bytes: 0,
            copied_bytes: 0,
            start_time: 0.0,
            end_time: 0.0,
            speed_mib_s: 0.0,
            data_mib_s: 0.0,
            data_elapsed_s: 0.0,
            errors: Vec::new(),
            hash_verifications: 0,
            hash_failures: 0,
            files: Vec::new(),
        }
    }
}

/// Enhanced copy job with multi-destination support
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct CopyJob {
    #[pyo3(get, set)]
    pub source_paths: Vec<String>,
    #[pyo3(get, set)]
    pub destination_paths: Vec<String>,
    #[pyo3(get, set)]
    pub destinations: Vec<CopyDestination>,
    #[pyo3(get, set)]
    pub block_size: usize,
    #[pyo3(get, set)]
    pub thread_count: usize,
    #[pyo3(get, set)]
    pub use_direct_io: bool,
    #[pyo3(get, set)]
    pub verify_integrity: bool,
    #[pyo3(get, set)]
    pub hash_algorithm: String,
    #[pyo3(get, set)]
    pub mtu_size: usize,
    #[pyo3(get, set)]
    pub socket_buffer_size: usize,
    #[pyo3(get, set)]
    pub adaptive_parameters: bool,
    #[pyo3(get, set)]
    pub large_file_threshold: u64,
    #[pyo3(get, set)]
    pub files_in_flight: usize,
    #[pyo3(get, set)]
    pub ranges_per_file: usize,
    #[pyo3(get, set)]
    pub preset: String,
    #[pyo3(get, set)]
    pub verify_mode: String,
    #[pyo3(get, set)]
    pub per_dest_params: Vec<TunedParams>,
    #[pyo3(get, set)]
    pub generate_verification_report: bool,
    #[pyo3(get, set)]
    pub job_id: String,
    #[pyo3(get, set)]
    pub reports_folder_name: String,
    #[pyo3(get, set)]
    pub cloud_source: bool,
}

#[pymethods]
impl CopyJob {
    #[new]
    fn new() -> Self {
        Self::default()
    }
}

impl Default for CopyJob {
    fn default() -> Self {
        Self {
            source_paths: Vec::new(),
            destination_paths: Vec::new(),
            destinations: Vec::new(),
            block_size: 4 * 1024 * 1024,
            thread_count: 0,
            use_direct_io: false,
            verify_integrity: false,
            hash_algorithm: "xxhash64".to_string(),
            mtu_size: 0,
            socket_buffer_size: 0,
            adaptive_parameters: true,
            large_file_threshold: 256 * 1024 * 1024,
            files_in_flight: 1,
            ranges_per_file: 1,
            preset: "auto".to_string(),
            verify_mode: "FAST".to_string(),
            per_dest_params: Vec::new(),
            generate_verification_report: true,
            job_id: String::new(),
            reports_folder_name: "_ForwardFlow_verification_Reports".to_string(),
            cloud_source: false,
        }
    }
}

/// Destination progress payload for UI updates
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct DestProgressPayload {
    #[pyo3(get, set)]
    pub dest_index: usize,
    #[pyo3(get, set)]
    pub dest_path: String,
    #[pyo3(get, set)]
    pub transfer_type: String,
    #[pyo3(get, set)]
    pub bytes_copied: u64,
    #[pyo3(get, set)]
    pub total_bytes: u64,
    #[pyo3(get, set)]
    pub current_speed_mib_s: f64,
    #[pyo3(get, set)]
    pub peak_speed_mib_s: f64,
    #[pyo3(get, set)]
    pub elapsed_time: f64,
    #[pyo3(get, set)]
    pub completed_files: usize,
    #[pyo3(get, set)]
    pub total_files: usize,
}

impl Default for DestProgressPayload {
    fn default() -> Self {
        Self {
            dest_index: 0,
            dest_path: String::new(),
            transfer_type: String::new(),
            bytes_copied: 0,
            total_bytes: 0,
            current_speed_mib_s: 0.0,
            peak_speed_mib_s: 0.0,
            elapsed_time: 0.0,
            completed_files: 0,
            total_files: 0,
        }
    }
}

/// Enhanced file transfer record for industry-standard reporting
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct FileTransferRecord {
    #[pyo3(get, set)]
    pub source_path: String,
    #[pyo3(get, set)]
    pub destination_path: String,
    #[pyo3(get, set)]
    pub filename: String,
    #[pyo3(get, set)]
    pub file_size: u64,
    #[pyo3(get, set)]
    pub checksum_source: String,
    #[pyo3(get, set)]
    pub checksum_destination: String,
    #[pyo3(get, set)]
    pub status: String,
    #[pyo3(get, set)]
    pub error_message: String,
    #[pyo3(get, set)]
    pub transfer_speed_mib_s: f64,
    #[pyo3(get, set)]
    pub verification_passed: bool,
    #[pyo3(get, set)]
    pub verification_error: String,
}

impl Default for FileTransferRecord {
    fn default() -> Self {
        Self {
            source_path: String::new(),
            destination_path: String::new(),
            filename: String::new(),
            file_size: 0,
            checksum_source: String::new(),
            checksum_destination: String::new(),
            status: "IN_PROGRESS".to_string(),
            error_message: String::new(),
            transfer_speed_mib_s: 0.0,
            verification_passed: false,
            verification_error: String::new(),
        }
    }
}

/// Enhanced copy stats with detailed file information
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct EnhancedCopyStats {
    #[pyo3(get, set)]
    pub total_files: u64,
    #[pyo3(get, set)]
    pub completed_files: u64,
    #[pyo3(get, set)]
    pub cancelled_files: u64,
    #[pyo3(get, set)]
    pub error_files: u64,
    #[pyo3(get, set)]
    pub total_bytes: u64,
    #[pyo3(get, set)]
    pub completed_bytes: u64,
    #[pyo3(get, set)]
    pub average_speed_mib_s: f64,
    #[pyo3(get, set)]
    pub file_records: Vec<FileTransferRecord>,
}

impl Default for EnhancedCopyStats {
    fn default() -> Self {
        Self {
            total_files: 0,
            completed_files: 0,
            cancelled_files: 0,
            error_files: 0,
            total_bytes: 0,
            completed_bytes: 0,
            average_speed_mib_s: 0.0,
            file_records: Vec::new(),
        }
    }
}

/// Progress gate for throttling events
pub struct ProgressGate {
    last_ns: HashMap<String, u64>,
}

impl ProgressGate {
    pub fn new() -> Self {
        Self {
            last_ns: HashMap::new(),
        }
    }
    
    pub fn now_ns() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos() as u64
    }
    
    pub fn should_emit(&mut self, key: &str, interval_ns: u64) -> bool {
        let now = Self::now_ns();
        let last = self.last_ns.get(key).copied().unwrap_or(0);
        
        if now - last >= interval_ns {
            self.last_ns.insert(key.to_string(), now);
            true
        } else {
            false
        }
    }
}

/// Register Python types for this module
pub fn register_python_types(m: &PyModule) -> PyResult<()> {
    m.add_class::<CopyDestination>()?;
    m.add_class::<TunedParams>()?;
    m.add_class::<CopyStats>()?;
    m.add_class::<CopyJob>()?;
    m.add_class::<DestProgressPayload>()?;
    m.add_class::<FileTransferRecord>()?;
    m.add_class::<EnhancedCopyStats>()?;
    Ok(())
}
