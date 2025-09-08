//! Progress tracking and statistics management

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use pyo3::prelude::*;

use crate::data_structures::{CopyStats, EnhancedCopyStats, FileTransferRecord, DestProgressPayload};

/// Performance metrics for a transfer operation
#[derive(Debug, Clone)]
pub struct PerformanceMetrics {
    pub start_time: Instant,
    pub last_update: Instant,
    pub bytes_transferred: u64,
    pub files_completed: usize,
    pub current_speed_mib_s: f64,
    pub peak_speed_mib_s: f64,
    pub average_speed_mib_s: f64,
    pub estimated_time_remaining: Option<Duration>,
}

impl PerformanceMetrics {
    pub fn new() -> Self {
        let now = Instant::now();
        Self {
            start_time: now,
            last_update: now,
            bytes_transferred: 0,
            files_completed: 0,
            current_speed_mib_s: 0.0,
            peak_speed_mib_s: 0.0,
            average_speed_mib_s: 0.0,
            estimated_time_remaining: None,
        }
    }
    
    /// Update metrics with new data
    pub fn update(&mut self, bytes_transferred: u64, files_completed: usize) {
        let now = Instant::now();
        let time_since_last = now.duration_since(self.last_update);
        
        if time_since_last.as_secs_f64() > 0.0 {
            let bytes_diff = bytes_transferred.saturating_sub(self.bytes_transferred);
            let speed_mib_s = (bytes_diff as f64 / time_since_last.as_secs_f64()) / (1024.0 * 1024.0);
            
            self.current_speed_mib_s = speed_mib_s;
            if speed_mib_s > self.peak_speed_mib_s {
                self.peak_speed_mib_s = speed_mib_s;
            }
        }
        
        self.bytes_transferred = bytes_transferred;
        self.files_completed = files_completed;
        self.last_update = now;
        
        // Calculate average speed
        let total_time = now.duration_since(self.start_time);
        if total_time.as_secs_f64() > 0.0 {
            self.average_speed_mib_s = (bytes_transferred as f64 / total_time.as_secs_f64()) / (1024.0 * 1024.0);
        }
        
        // Estimate time remaining (simplified)
        self.estimated_time_remaining = None; // Would calculate based on remaining work
    }
    
    /// Get elapsed time
    pub fn elapsed_time(&self) -> Duration {
        self.last_update.duration_since(self.start_time)
    }
    
    /// Get progress percentage
    pub fn progress_percentage(&self, total_bytes: u64) -> f64 {
        if total_bytes > 0 {
            (self.bytes_transferred as f64 / total_bytes as f64) * 100.0
        } else {
            0.0
        }
    }
}

/// Destination-specific progress tracking
#[derive(Debug, Clone)]
pub struct DestinationProgress {
    pub path: String,
    pub metrics: PerformanceMetrics,
    pub status: TransferStatus,
    pub error_count: usize,
    pub last_error: Option<String>,
}

impl DestinationProgress {
    pub fn new(path: String) -> Self {
        Self {
            path,
            metrics: PerformanceMetrics::new(),
            status: TransferStatus::Idle,
            error_count: 0,
            last_error: None,
        }
    }
    
    /// Update progress for this destination
    pub fn update_progress(&mut self, bytes_transferred: u64, files_completed: usize) {
        self.metrics.update(bytes_transferred, files_completed);
        self.status = TransferStatus::Active;
    }
    
    /// Mark as completed
    pub fn mark_completed(&mut self) {
        self.status = TransferStatus::Completed;
    }
    
    /// Mark as failed
    pub fn mark_failed(&mut self, error: String) {
        self.status = TransferStatus::Failed;
        self.error_count += 1;
        self.last_error = Some(error);
    }
    
    /// Mark as paused
    pub fn mark_paused(&mut self) {
        self.status = TransferStatus::Paused;
    }
}

/// Transfer status enumeration
#[derive(Debug, Clone, PartialEq)]
pub enum TransferStatus {
    Idle,
    Active,
    Paused,
    Completed,
    Failed,
    Cancelled,
}

impl TransferStatus {
    pub fn to_string(&self) -> String {
        match self {
            TransferStatus::Idle => "IDLE".to_string(),
            TransferStatus::Active => "ACTIVE".to_string(),
            TransferStatus::Paused => "PAUSED".to_string(),
            TransferStatus::Completed => "COMPLETED".to_string(),
            TransferStatus::Failed => "FAILED".to_string(),
            TransferStatus::Cancelled => "CANCELLED".to_string(),
        }
    }
}

/// Progress tracker for managing overall transfer progress
pub struct ProgressTracker {
    overall_metrics: Arc<Mutex<PerformanceMetrics>>,
    destination_progress: Arc<Mutex<HashMap<String, DestinationProgress>>>,
    file_records: Arc<Mutex<Vec<FileTransferRecord>>>,
    start_time: SystemTime,
}

impl ProgressTracker {
    pub fn new() -> Self {
        Self {
            overall_metrics: Arc::new(Mutex::new(PerformanceMetrics::new())),
            destination_progress: Arc::new(Mutex::new(HashMap::new())),
            file_records: Arc::new(Mutex::new(Vec::new())),
            start_time: SystemTime::now(),
        }
    }
    
    /// Update overall progress
    pub fn update_overall_progress(&self, bytes_transferred: u64, files_completed: usize) {
        if let Ok(mut metrics) = self.overall_metrics.lock() {
            metrics.update(bytes_transferred, files_completed);
        }
    }
    
    /// Update destination progress
    pub fn update_destination_progress(
        &self,
        destination_path: &str,
        bytes_transferred: u64,
        files_completed: usize,
    ) {
        if let Ok(mut dest_progress) = self.destination_progress.lock() {
            let progress = dest_progress
                .entry(destination_path.to_string())
                .or_insert_with(|| DestinationProgress::new(destination_path.to_string()));
            
            progress.update_progress(bytes_transferred, files_completed);
        }
    }
    
    /// Mark destination as completed
    pub fn mark_destination_completed(&self, destination_path: &str) {
        if let Ok(mut dest_progress) = self.destination_progress.lock() {
            if let Some(progress) = dest_progress.get_mut(destination_path) {
                progress.mark_completed();
            }
        }
    }
    
    /// Mark destination as failed
    pub fn mark_destination_failed(&self, destination_path: &str, error: String) {
        if let Ok(mut dest_progress) = self.destination_progress.lock() {
            if let Some(progress) = dest_progress.get_mut(destination_path) {
                progress.mark_failed(error);
            }
        }
    }
    
    /// Add file transfer record
    pub fn add_file_record(&self, record: FileTransferRecord) {
        if let Ok(mut records) = self.file_records.lock() {
            records.push(record);
        }
    }
    
    /// Get overall copy stats
    pub fn get_copy_stats(&self) -> CopyStats {
        if let Ok(metrics) = self.overall_metrics.lock() {
            let elapsed = metrics.elapsed_time().as_secs_f64();
            CopyStats {
                total_files: 0, // Would track total files
                copied_files: metrics.files_completed,
                total_bytes: 0, // Would track total bytes
                copied_bytes: metrics.bytes_transferred,
                start_time: self.start_time.duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64(),
                end_time: SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64(),
                speed_mib_s: metrics.current_speed_mib_s,
                data_mib_s: metrics.average_speed_mib_s,
                data_elapsed_s: elapsed,
                errors: Vec::new(), // Would track errors
                hash_verifications: 0, // Would track verifications
                hash_failures: 0, // Would track failures
                files: Vec::new(), // Will be populated by engine
            }
        } else {
            CopyStats::default()
        }
    }
    
    /// Get enhanced copy stats
    pub fn get_enhanced_stats(&self) -> EnhancedCopyStats {
        let file_records = if let Ok(records) = self.file_records.lock() {
            records.clone()
        } else {
            Vec::new()
        };
        
        let total_files = file_records.len() as u64;
        let completed_files = file_records.iter().filter(|r| r.status == "COMPLETED").count() as u64;
        let error_files = file_records.iter().filter(|r| r.status == "ERROR").count() as u64;
        let total_bytes = file_records.iter().map(|r| r.file_size).sum();
        let completed_bytes = file_records.iter().filter(|r| r.status == "COMPLETED").map(|r| r.file_size).sum();
        
        let average_speed = if let Ok(metrics) = self.overall_metrics.lock() {
            metrics.average_speed_mib_s
        } else {
            0.0
        };
        
        EnhancedCopyStats {
            total_files,
            completed_files,
            cancelled_files: 0, // Would track cancelled files
            error_files,
            total_bytes,
            completed_bytes,
            average_speed_mib_s: average_speed,
            file_records,
        }
    }
    
    /// Get destination progress payload
    pub fn get_destination_progress(&self, dest_index: usize, dest_path: &str) -> Option<DestProgressPayload> {
        if let Ok(dest_progress) = self.destination_progress.lock() {
            if let Some(progress) = dest_progress.get(dest_path) {
                let elapsed = progress.metrics.elapsed_time().as_secs_f64();
                return Some(DestProgressPayload {
                    dest_index,
                    dest_path: dest_path.to_string(),
                    transfer_type: progress.status.to_string(),
                    bytes_copied: progress.metrics.bytes_transferred,
                    total_bytes: 0, // Would track total bytes for this destination
                    current_speed_mib_s: progress.metrics.current_speed_mib_s,
                    peak_speed_mib_s: progress.metrics.peak_speed_mib_s,
                    elapsed_time: elapsed,
                    completed_files: progress.metrics.files_completed,
                    total_files: 0, // Would track total files for this destination
                });
            }
        }
        None
    }
    
    /// Get all destination progress
    pub fn get_all_destination_progress(&self) -> Vec<DestProgressPayload> {
        let mut result = Vec::new();
        if let Ok(dest_progress) = self.destination_progress.lock() {
            for (index, (path, progress)) in dest_progress.iter().enumerate() {
                if let Some(payload) = self.get_destination_progress(index, path) {
                    result.push(payload);
                }
            }
        }
        result
    }
    
    /// Reset progress tracker
    pub fn reset(&mut self) {
        if let Ok(mut metrics) = self.overall_metrics.lock() {
            *metrics = PerformanceMetrics::new();
        }
        if let Ok(mut dest_progress) = self.destination_progress.lock() {
            dest_progress.clear();
        }
        if let Ok(mut file_records) = self.file_records.lock() {
            file_records.clear();
        }
        self.start_time = SystemTime::now();
    }
}

/// Python wrapper for ProgressTracker
#[pyclass]
pub struct PyProgressTracker {
    inner: Arc<Mutex<ProgressTracker>>,
}

#[pymethods]
impl PyProgressTracker {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(ProgressTracker::new())),
        }
    }
    
    fn update_overall_progress(&self, bytes_transferred: u64, files_completed: usize) {
        if let Ok(tracker) = self.inner.lock() {
            tracker.update_overall_progress(bytes_transferred, files_completed);
        }
    }
    
    fn update_destination_progress(&self, destination_path: String, bytes_transferred: u64, files_completed: usize) {
        if let Ok(tracker) = self.inner.lock() {
            tracker.update_destination_progress(&destination_path, bytes_transferred, files_completed);
        }
    }
    
    fn get_copy_stats(&self) -> PyResult<CopyStats> {
        if let Ok(tracker) = self.inner.lock() {
            Ok(tracker.get_copy_stats())
        } else {
            Ok(CopyStats::default())
        }
    }
    
    fn get_enhanced_stats(&self) -> PyResult<EnhancedCopyStats> {
        if let Ok(tracker) = self.inner.lock() {
            Ok(tracker.get_enhanced_stats())
        } else {
            Ok(EnhancedCopyStats::default())
        }
    }
    
    fn get_destination_progress(&self, dest_index: usize, dest_path: String) -> PyResult<Option<DestProgressPayload>> {
        if let Ok(tracker) = self.inner.lock() {
            Ok(tracker.get_destination_progress(dest_index, &dest_path))
        } else {
            Ok(None)
        }
    }
    
    fn reset(&mut self) {
        if let Ok(mut tracker) = self.inner.lock() {
            tracker.reset();
        }
    }
}

/// Register Python types for this module
pub fn register_python_types(m: &PyModule) -> PyResult<()> {
    m.add_class::<PyProgressTracker>()?;
    Ok(())
}
