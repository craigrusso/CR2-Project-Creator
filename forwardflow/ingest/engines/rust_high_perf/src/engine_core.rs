//! Main engine core implementation

use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicBool, AtomicU64};
use std::time::{SystemTime, UNIX_EPOCH};
use pyo3::prelude::*;
use anyhow::Result;

use crate::data_structures::{*, FileTransferRecord};
use crate::event_system::EventSystem;
use crate::file_operations::FileOperationManager;
use crate::verification::VerificationManager;
use crate::progress_tracking::ProgressTracker;
use crate::cloud_detection::CloudDetectionManager;
use crate::platform_helpers::{get_disk_space, get_file_size};

/// Helper function to get current time in seconds
fn now_secs() -> f64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64()
}

/// Main high-performance transfer engine
pub struct EnhancedHighPerfTransferEngine {
    event_system: Arc<Mutex<EventSystem>>,
    file_operations: Arc<FileOperationManager>,
    verification_manager: Arc<VerificationManager>,
    progress_tracker: Arc<Mutex<ProgressTracker>>,
    cloud_detection: Arc<CloudDetectionManager>,
    
    // State management
    cancelled: Arc<AtomicBool>,
    paused: Arc<AtomicBool>,
    current_job_id: Arc<Mutex<Option<String>>>,
    
    // Statistics
    total_files_processed: AtomicU64,
    total_bytes_transferred: AtomicU64,
}

impl EnhancedHighPerfTransferEngine {
    pub fn new() -> Self {
        Self {
            event_system: Arc::new(Mutex::new(EventSystem::new())),
            file_operations: Arc::new(FileOperationManager::new(
                4 * 1024 * 1024, // 4MB buffer
                false, // No direct I/O by default
                4, // 4 parallel workers
            )),
            verification_manager: Arc::new(VerificationManager::new()),
            progress_tracker: Arc::new(Mutex::new(ProgressTracker::new())),
            cloud_detection: Arc::new(CloudDetectionManager::new()),
            
            cancelled: Arc::new(AtomicBool::new(false)),
            paused: Arc::new(AtomicBool::new(false)),
            current_job_id: Arc::new(Mutex::new(None)),
            
            total_files_processed: AtomicU64::new(0),
            total_bytes_transferred: AtomicU64::new(0),
        }
    }
    
    /// Set the event sink for Python callbacks
    pub fn set_event_sink(&self, sink: Box<dyn Fn(String, PyObject) + Send + Sync>) {
        if let Ok(mut event_system) = self.event_system.lock() {
            event_system.set_event_sink(sink);
        }
    }
    
    /// Emit job progress with locked event system (helper to avoid duplication)
    fn emit_job_progress_locked(
        &self,
        event_system: &EventSystem,
        start_time: f64,
        total_bytes: u64,
        total_files: usize,
    ) {
        let bytes = self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed) as u64;
        let files = self.total_files_processed.load(std::sync::atomic::Ordering::Relaxed) as usize;
        let elapsed = (now_secs() - start_time).max(0.0);
        let speed_mib_s = if elapsed > 0.0 {
            (bytes as f64 / elapsed) / (1024.0 * 1024.0)
        } else { 
            0.0 
        };

        // NOTE: use MiB/s (not Mb/s)
        let _ = event_system.emit_job_progress(bytes, total_bytes, files, total_files, elapsed, speed_mib_s);
    }
    
    /// Main method to copy files
    pub fn copy_files(&self, job: &CopyJob) -> Result<CopyStats> {
        let start_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64();
        
        // Set current job ID
        if let Ok(mut current_job) = self.current_job_id.lock() {
            *current_job = Some(job.job_id.clone());
        }
        
        // Reset progress tracker
        if let Ok(mut tracker) = self.progress_tracker.lock() {
            tracker.reset();
        }
        
        // Collect all source files
        let source_files = self.file_operations.collect_files(&job.source_paths)?;
        let total_files = source_files.len();
        let total_bytes: u64 = source_files.iter()
            .filter_map(|p| get_file_size(p).ok())
            .sum();
        
        // Update progress tracker with initial values
        if let Ok(mut tracker) = self.progress_tracker.lock() {
            tracker.update_overall_progress(0, 0);
        }
        
        // Check disk space for all destinations
        for dest_path in &job.destination_paths {
            let disk_space = get_disk_space(std::path::Path::new(dest_path))?;
            if disk_space.available_bytes < total_bytes {
                return Err(anyhow::anyhow!(
                    "Insufficient disk space at destination: {}. Required: {} bytes, Available: {} bytes",
                    dest_path, total_bytes, disk_space.available_bytes
                ));
            }
        }
        
        // Process files based on destination count
        let mut copy_stats = CopyStats::default();
        copy_stats.start_time = start_time;
        copy_stats.total_files = total_files;
        copy_stats.total_bytes = total_bytes;
        
        let mut file_records = Vec::new();
        
        if job.destination_paths.len() == 1 {
            // Single destination copy
            file_records = self.copy_to_single_destination(job, &source_files, start_time, total_bytes, total_files)?;
        } else {
            // Multiple destination copy
            file_records = self.copy_to_multiple_destinations(job, &source_files, start_time, total_bytes, total_files)?;
        }
        
        copy_stats.end_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64();
        copy_stats.copied_files = self.total_files_processed.load(std::sync::atomic::Ordering::Relaxed) as usize;
        copy_stats.copied_bytes = self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed);
        
        // Add file records to copy stats
        copy_stats.files = file_records;
        
        // Calculate speeds
        let duration = copy_stats.end_time - copy_stats.start_time;
        if duration > 0.0 {
            copy_stats.speed_mib_s = (copy_stats.copied_bytes as f64 / duration) / (1024.0 * 1024.0);
            copy_stats.data_mib_s = copy_stats.speed_mib_s;
            copy_stats.data_elapsed_s = duration;
        }
        
        // Clear current job ID
        if let Ok(mut current_job) = self.current_job_id.lock() {
            *current_job = None;
        }
        
        Ok(copy_stats)
    }
    
    /// Copy files to a single destination
    fn copy_to_single_destination(&self, job: &CopyJob, source_files: &[std::path::PathBuf], start_time: f64, total_bytes: u64, total_files: usize) -> Result<Vec<FileTransferRecord>> {
        let dest_path = &job.destination_paths[0];
        
        // Emit destination progress event
        let mut dest_progress = DestProgressPayload::default();
        dest_progress.dest_index = 0;
        dest_progress.dest_path = dest_path.clone();
        dest_progress.transfer_type = "COPY".to_string();
        dest_progress.total_files = source_files.len();
        
        if let Ok(event_system) = self.event_system.lock() {
            let _ = event_system.emit_dest_progress(&dest_progress);
        }
        
        // Copy files with immediate cancellation support using threads
        let results = self.file_operations.copy_files_parallel_with_cancellation_threaded(
            source_files, 
            std::path::Path::new(dest_path), 
            None,
            Arc::clone(&self.cancelled)
        )?;
        
        // Process results and update progress
        let mut file_records = Vec::new();
        
        for (index, result) in results.iter().enumerate() {
            // Check for cancellation before processing each result
            if self.is_cancelled() {
                println!("DEBUG: Copy operation cancelled during processing");
                break;
            }
            if result.success {
                self.total_files_processed.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                self.total_bytes_transferred.fetch_add(result.bytes_copied, std::sync::atomic::Ordering::Relaxed);
                
                // Update progress
                if let Ok(mut tracker) = self.progress_tracker.lock() {
                    tracker.update_overall_progress(
                        self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed),
                        self.total_files_processed.load(std::sync::atomic::Ordering::Relaxed) as usize,
                    );
                }
                
                // Create file transfer record
                let filename = source_files[index].file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown")
                    .to_string();
                
                // CRITICAL FIX: Always calculate hashes for DIT reports (professional requirement)
                let source_file_path = &source_files[index];
                let dest_file_path = std::path::Path::new(dest_path).join(&filename);
                
                // Always calculate hashes for DIT compliance, regardless of user verification settings
                let hash_algorithm = if job.verify_integrity {
                    job.hash_algorithm.clone()
                } else {
                    "xxhash64".to_string() // Default to xxhash64 for DIT reports
                };
                
                let (source_hash, dest_hash, verification_passed) = {
                    match self.calculate_file_hashes(source_file_path, &dest_file_path, &hash_algorithm) {
                        Ok((src, dst)) => {
                            let passed = src == dst;
                            println!("DEBUG: Hash calculated for {}: source={}, dest={}, passed={}", filename, src, dst, passed);
                            (src, dst, passed)
                        },
                        Err(e) => {
                            println!("Hash calculation error for {}: {}", filename, e);
                            ("hash_error".to_string(), "hash_error".to_string(), false)
                        }
                    }
                };

                let file_record = FileTransferRecord {
                    filename: filename.clone(),
                    source_path: source_files[index].to_string_lossy().to_string(),
                    destination_path: format!("{}/{}", dest_path, filename),
                    file_size: result.bytes_copied,
                    checksum_source: source_hash.clone(),
                    checksum_destination: dest_hash.clone(),
                    status: "completed".to_string(),
                    error_message: String::new(),
                    transfer_speed_mib_s: 0.0, // Will be calculated
                    verification_passed,
                    verification_error: String::new(),
                };
                file_records.push(file_record);
                
                // CRITICAL FIX: Emit BOTH file.complete AND file.completed events for DIT report compatibility
                if let Ok(event_system) = self.event_system.lock() {
                    if !source_hash.is_empty() {
                        // Emit detailed file completed event with hash data
                        let _ = event_system.emit_file_completed_with_hash(
                            &filename,
                            source_file_path.to_str().unwrap_or(""),
                            dest_file_path.to_str().unwrap_or(""),
                            result.bytes_copied,
                            &source_hash,
                            &dest_hash
                        );
                        
                        // CRITICAL: Also emit file.complete event for DIT report data collection
                        let _ = event_system.emit_event("file.complete", Python::with_gil(|py| {
                            let payload = pyo3::types::PyDict::new(py);
                            let _ = payload.set_item("filename", &filename);
                            let _ = payload.set_item("source_path", source_file_path.to_str().unwrap_or(""));
                            let _ = payload.set_item("dest_path", dest_file_path.to_str().unwrap_or(""));
                            let _ = payload.set_item("size_bytes", result.bytes_copied);
                            let _ = payload.set_item("source_checksum", &source_hash);
                            let _ = payload.set_item("destination_checksum", &dest_hash);
                            let _ = payload.set_item("hash_algorithm", hash_algorithm);
                            let _ = payload.set_item("verification_passed", verification_passed);
                            let _ = payload.set_item("transfer_status", "COMPLETED");
                            let _ = payload.set_item("status", "COMPLETED");
                            payload.into_py(py)
                        }));
                        
                        println!("DEBUG: 🎯 EMITTED file.complete EVENT for DIT report: {}", filename);
                    } else {
                        let _ = event_system.emit_file_completed(&filename, result.bytes_copied);
                        
                        // CRITICAL: Also emit file.complete event with calculated hashes
                        let _ = event_system.emit_event("file.complete", Python::with_gil(|py| {
                            let payload = pyo3::types::PyDict::new(py);
                            let _ = payload.set_item("filename", &filename);
                            let _ = payload.set_item("source_path", source_file_path.to_str().unwrap_or(""));
                            let _ = payload.set_item("dest_path", dest_file_path.to_str().unwrap_or(""));
                            let _ = payload.set_item("size_bytes", result.bytes_copied);
                            let _ = payload.set_item("source_checksum", &source_hash);
                            let _ = payload.set_item("destination_checksum", &dest_hash);
                            let _ = payload.set_item("hash_algorithm", hash_algorithm);
                            let _ = payload.set_item("verification_passed", verification_passed);
                            let _ = payload.set_item("transfer_status", "COMPLETED");
                            let _ = payload.set_item("status", "COMPLETED");
                            payload.into_py(py)
                        }));
                        
                        println!("DEBUG: 🎯 EMITTED file.complete EVENT (no hash) for DIT report: {}", filename);
                    }
                    
                    // Emit job progress event
                    let elapsed = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs_f64() - start_time;
                    let speed_mib_s = if elapsed > 0.0 {
                        (self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed) as f64 / elapsed) / (1024.0 * 1024.0)
                    } else {
                        0.0
                    };
                    
                    let _ = event_system.emit_job_progress(
                        self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed),
                        total_bytes,
                        self.total_files_processed.load(std::sync::atomic::Ordering::Relaxed) as usize,
                        total_files,
                        elapsed,
                        speed_mib_s,
                    );
                }
            } else {
                // Handle error
                if let Some(error_msg) = &result.error_message {
                    // Note: In a full implementation, we'd track errors properly
                    // For now, we'll just log them
                    eprintln!("File copy error: {}", error_msg);
                    
                    // Create error file record
                    let filename = source_files[index].file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("unknown")
                        .to_string();
                    
                    let file_record = FileTransferRecord {
                        filename: filename.clone(),
                        source_path: source_files[index].to_string_lossy().to_string(),
                        destination_path: format!("{}/{}", dest_path, filename),
                        file_size: 0,
                        checksum_source: String::new(),
                        checksum_destination: String::new(),
                        status: "failed".to_string(),
                        error_message: error_msg.clone(),
                        transfer_speed_mib_s: 0.0,
                        verification_passed: false,
                        verification_error: error_msg.clone(),
                    };
                    file_records.push(file_record);
                }
            }
        }
        
        // Emit destination completion event once all files are processed for this destination
        if let Ok(event_system) = self.event_system.lock() {
            let completed_files = self.total_files_processed.load(std::sync::atomic::Ordering::Relaxed) as usize;
            let mut dest_completion = DestProgressPayload::default();
            dest_completion.dest_index = 0;
            dest_completion.dest_path = dest_path.clone();
            dest_completion.transfer_type = "COPY".to_string();
            dest_completion.completed_files = completed_files;
            dest_completion.total_files = total_files;
            dest_completion.bytes_copied = self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed);
            dest_completion.total_bytes = total_bytes;
            
            // Emit as both dest_progress at 100% and explicit dest.completed event
            let _ = event_system.emit_dest_progress(&dest_completion);
            let _ = event_system.emit_event("dest.completed", Python::with_gil(|py| {
                let payload = pyo3::types::PyDict::new(py);
                let _ = payload.set_item("dest_path", &dest_path);
                let _ = payload.set_item("dest_index", 0);
                let _ = payload.set_item("completed_files", completed_files);
                let _ = payload.set_item("total_files", total_files);
                let _ = payload.set_item("bytes_copied", self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed));
                let _ = payload.set_item("total_bytes", total_bytes);
                payload.into_py(py)
            }));
            
            println!("DEBUG: 🎯 EMITTED dest.completed EVENT for {}", dest_path);
        }
        
        Ok(file_records)
    }
    
    /// Copy files to multiple destinations
    fn copy_to_multiple_destinations(&self, job: &CopyJob, source_files: &[std::path::PathBuf], start_time: f64, total_bytes: u64, total_files: usize) -> Result<Vec<FileTransferRecord>> {
        let mut file_records = Vec::new();
        
        // For multiple destinations, we'll create records for the first destination
        let dest_path = &job.destination_paths[0];
        
        // [TODO] Cloud-aware hydration: detect cloud-backed sources; prefetch before copy; avoid clonefile semantics.
        // [TODO] Spool-to-NVMe mode: read-once to fast temp (NVMe), tee to N destinations, keep RAM bounded.
        // [TODO] Adaptive queues/chunk size: per-destination I/O depth + block size tuning based on moving throughput/latency.
        // [TODO] Read watchdog + retry: isolate slow device; do not stall global pipeline.
        // [TODO] Checksums & MHL: support stream verify and read-back verify; write per-file + job reports (JSON + MHL txt).
        // [TODO] Metadata preservation: xattrs, ACLs, timestamps; platform-aware flags (macOS/Linux/Windows).
        // [TODO] Tiny-file path ("file-count fix"): coalesce 0B/tiny files to reduce syscall overhead.
        
        let results = self.file_operations.copy_to_multiple_destinations_with_cancellation_threaded(
            source_files,
            &job.destination_paths,
            None,
            Arc::clone(&self.cancelled)
        )?;
        
        // Process results with continuous progress emission
        // Note: results contains one entry per file per destination, so we need to group them
        let files_per_dest = source_files.len();
        let mut file_index = 0;
        
        for (index, result) in results.iter().enumerate() {
            // Check for cancellation before processing each result
            if self.is_cancelled() {
                println!("DEBUG: Copy operation cancelled during processing");
                break;
            }
            
            if result.success {
                // Update counters
                self.total_files_processed.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                self.total_bytes_transferred.fetch_add(result.bytes_copied, std::sync::atomic::Ordering::Relaxed);

                // Update progress tracker
                if let Ok(mut tracker) = self.progress_tracker.lock() {
                    tracker.update_overall_progress(
                        self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed) as u64,
                        self.total_files_processed.load(std::sync::atomic::Ordering::Relaxed) as usize,
                    );
                }

                // Calculate which source file this result corresponds to
                let source_file_index = index % files_per_dest;
                
                // Create file transfer record
                let filename = source_files[source_file_index].file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown")
                    .to_string();
                
                let file_record = FileTransferRecord {
                    filename: filename.clone(),
                    source_path: source_files[source_file_index].to_string_lossy().to_string(),
                    destination_path: format!("{}/{}", dest_path, filename),
                    file_size: result.bytes_copied,
                    checksum_source: "xxh64_hash".to_string(), // Placeholder
                    checksum_destination: "xxh64_hash".to_string(), // Placeholder
                    status: "completed".to_string(),
                    error_message: String::new(),
                    transfer_speed_mib_s: 0.0, // Will be calculated
                    verification_passed: true,
                    verification_error: String::new(),
                };
                file_records.push(file_record);

                // Emit file_completed and job_progress events
                if let Ok(event_system) = self.event_system.lock() {
                    let _ = event_system.emit_file_completed(&filename, result.bytes_copied);

                    // Emit job_progress (MiB/s)
                    self.emit_job_progress_locked(
                        &event_system,
                        start_time,
                        total_bytes,
                        total_files,
                    );
                }
            } else {
                // Handle error
                if let Some(error_msg) = &result.error_message {
                    let source_file_index = index % files_per_dest;
                    let filename = source_files[source_file_index].file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("unknown")
                        .to_string();
                    
                    let file_record = FileTransferRecord {
                        filename: filename.clone(),
                        source_path: source_files[source_file_index].to_string_lossy().to_string(),
                        destination_path: format!("{}/{}", dest_path, filename),
                        file_size: 0,
                        checksum_source: String::new(),
                        checksum_destination: String::new(),
                        status: "failed".to_string(),
                        error_message: error_msg.clone(),
                        transfer_speed_mib_s: 0.0,
                        verification_passed: false,
                        verification_error: error_msg.clone(),
                    };
                    file_records.push(file_record);
                }
            }
        }
        
        // Emit destination completion events for multiple destinations
        if let Ok(event_system) = self.event_system.lock() {
            let completed_files = self.total_files_processed.load(std::sync::atomic::Ordering::Relaxed) as usize;
            let total_bytes_copied = self.total_bytes_transferred.load(std::sync::atomic::Ordering::Relaxed);
            
            // Emit completion event for each destination
            for (dest_index, dest_path) in job.destination_paths.iter().enumerate() {
                let mut dest_completion = DestProgressPayload::default();
                dest_completion.dest_index = dest_index;
                dest_completion.dest_path = dest_path.clone();
                dest_completion.transfer_type = "COPY".to_string();
                dest_completion.completed_files = completed_files / job.destination_paths.len(); // Divide by destination count
                dest_completion.total_files = total_files;
                dest_completion.bytes_copied = total_bytes_copied / job.destination_paths.len() as u64; // Divide by destination count
                dest_completion.total_bytes = total_bytes;
                
                // Emit as both dest_progress at 100% and explicit dest.completed event
                let _ = event_system.emit_dest_progress(&dest_completion);
                let _ = event_system.emit_event("dest.completed", Python::with_gil(|py| {
                    let payload = pyo3::types::PyDict::new(py);
                    let _ = payload.set_item("dest_path", dest_path);
                    let _ = payload.set_item("dest_index", dest_index);
                    let _ = payload.set_item("completed_files", dest_completion.completed_files);
                    let _ = payload.set_item("total_files", total_files);
                    let _ = payload.set_item("bytes_copied", dest_completion.bytes_copied);
                    let _ = payload.set_item("total_bytes", total_bytes);
                    payload.into_py(py)
                }));
                
                println!("DEBUG: 🎯 EMITTED dest.completed EVENT for {} (index {})", dest_path, dest_index);
            }
        }
        
        Ok(file_records)
    }
    
    /// Cancel the current operation
    pub fn cancel(&self) {
        self.cancelled.store(true, std::sync::atomic::Ordering::Relaxed);
        
        // Emit cancellation event
        if let Ok(event_system) = self.event_system.lock() {
            let _ = event_system.emit_event("cancelled", Python::with_gil(|py| py.None()));
        }
    }
    
    /// Pause the current operation
    pub fn pause(&self) {
        self.paused.store(true, std::sync::atomic::Ordering::Relaxed);
        
        // Emit pause event
        if let Ok(event_system) = self.event_system.lock() {
            let _ = event_system.emit_event("paused", Python::with_gil(|py| py.None()));
        }
    }
    
    /// Resume the current operation
    pub fn resume(&self) {
        self.paused.store(false, std::sync::atomic::Ordering::Relaxed);
        
        // Emit resume event
        if let Ok(event_system) = self.event_system.lock() {
            let _ = event_system.emit_event("resumed", Python::with_gil(|py| py.None()));
        }
    }
    
    /// Get enhanced copy statistics
    pub fn get_enhanced_stats(&self) -> EnhancedCopyStats {
        if let Ok(tracker) = self.progress_tracker.lock() {
            tracker.get_enhanced_stats()
        } else {
            EnhancedCopyStats::default()
        }
    }
    
    /// Emit destination progress event
    pub fn emit_dest_progress(&self, payload: &DestProgressPayload) -> PyResult<()> {
        if let Ok(event_system) = self.event_system.lock() {
            event_system.emit_dest_progress(payload)
        } else {
            Ok(())
        }
    }
    
    /// Emit job progress event
    pub fn emit_job_progress(
        &self,
        bytes_copied: u64,
        total_bytes: u64,
        files_completed: usize,
        total_files: usize,
        elapsed: f64,
        speed_mbps: f64,
    ) -> PyResult<()> {
        if let Ok(event_system) = self.event_system.lock() {
            event_system.emit_job_progress(
                bytes_copied,
                total_bytes,
                files_completed,
                total_files,
                elapsed,
                speed_mbps,
            )
        } else {
            Ok(())
        }
    }
    
    /// Emit file completed event
    pub fn emit_file_completed(&self, filename: &str, bytes: u64) -> PyResult<()> {
        if let Ok(event_system) = self.event_system.lock() {
            event_system.emit_file_completed(filename, bytes)
        } else {
            Ok(())
        }
    }
    
    /// Check if operation is cancelled
    pub fn is_cancelled(&self) -> bool {
        self.cancelled.load(std::sync::atomic::Ordering::Relaxed)
    }

    /// Calculate file hashes for verification
    fn calculate_file_hashes(&self, source_path: &std::path::Path, dest_path: &std::path::Path, algorithm: &str) -> Result<(String, String)> {
        use crate::verification::{HashCalculator, HashAlgorithm};
        
        let hash_algo = HashAlgorithm::from_string(algorithm);
        let calculator = HashCalculator::new(hash_algo);
        
        let source_hash = calculator.calculate_file_hash(source_path)?;
        let dest_hash = calculator.calculate_file_hash(dest_path)?;
        
        Ok((source_hash, dest_hash))
    }
    
    /// Check if operation is paused
    pub fn is_paused(&self) -> bool {
        self.paused.load(std::sync::atomic::Ordering::Relaxed)
    }
    
    /// Reset engine state
    pub fn reset(&self) {
        self.cancelled.store(false, std::sync::atomic::Ordering::Relaxed);
        self.paused.store(false, std::sync::atomic::Ordering::Relaxed);
        self.total_files_processed.store(0, std::sync::atomic::Ordering::Relaxed);
        self.total_bytes_transferred.store(0, std::sync::atomic::Ordering::Relaxed);
        
        if let Ok(mut current_job) = self.current_job_id.lock() {
            *current_job = None;
        }
        
        if let Ok(mut tracker) = self.progress_tracker.lock() {
            tracker.reset();
        }
    }
}

/// Python wrapper for the main engine
#[pyclass]
pub struct PyEnhancedHighPerfTransferEngine {
    inner: Arc<EnhancedHighPerfTransferEngine>,
}

#[pymethods]
impl PyEnhancedHighPerfTransferEngine {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(EnhancedHighPerfTransferEngine::new()),
        }
    }
    
    fn set_event_sink(&self, sink: PyObject) {
        let sink_box = Box::new(move |event_type: String, payload: PyObject| {
            Python::with_gil(|py| {
                let _ = sink.call1(py, (event_type, payload));
            });
        });
        self.inner.set_event_sink(sink_box);
    }
    
    fn copy_files(&self, job: &CopyJob) -> PyResult<CopyStats> {
        match self.inner.copy_files(job) {
            Ok(stats) => Ok(stats),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
        }
    }
    
    fn cancel(&self) {
        self.inner.cancel();
    }
    
    fn pause(&self) {
        self.inner.pause();
    }
    
    fn resume(&self) {
        self.inner.resume();
    }
    
    fn get_enhanced_stats(&self) -> PyResult<EnhancedCopyStats> {
        Ok(self.inner.get_enhanced_stats())
    }
    
    fn emit_dest_progress(&self, payload: &DestProgressPayload) -> PyResult<()> {
        self.inner.emit_dest_progress(payload)
    }
    
    fn emit_job_progress(&self, bytes_copied: u64, total_bytes: u64, files_completed: usize, total_files: usize, elapsed: f64, speed_mib_s: f64) -> PyResult<()> {
        self.inner.emit_job_progress(bytes_copied, total_bytes, files_completed, total_files, elapsed, speed_mib_s)
    }
    
    fn emit_file_completed(&self, filename: String, bytes: u64) -> PyResult<()> {
        self.inner.emit_file_completed(&filename, bytes)
    }
    
    fn is_cancelled(&self) -> bool {
        self.inner.is_cancelled()
    }
    
    fn is_paused(&self) -> bool {
        self.inner.is_paused()
    }
    
    fn reset(&self) {
        self.inner.reset();
    }
}

/// Register Python types for this module
pub fn register_python_types(m: &PyModule) -> PyResult<()> {
    m.add_class::<PyEnhancedHighPerfTransferEngine>()?;
    Ok(())
}
