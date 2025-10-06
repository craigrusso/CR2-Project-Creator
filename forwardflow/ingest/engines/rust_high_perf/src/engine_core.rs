//! Main engine core implementation

use anyhow::Result;
use pyo3::prelude::*;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::cloud_detection::CloudDetectionManager;
use crate::data_structures::{FileTransferRecord, *};
use crate::event_system::EventSystem;
use crate::file_operations::FileOperationManager;
use crate::multi_dest_copy::MultiDestCopyEngine;
use crate::platform_helpers::{get_disk_space, get_file_size};
use crate::progress_tracking::ProgressTracker;
use crate::verification::{HashAlgorithm, VerificationManager};
use tracing::{debug, error};

/// Helper function to get current time in seconds
fn now_secs() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
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
                false,           // No direct I/O by default
                4,               // 4 parallel workers
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

    /// REMOVED: set_event_sink - now using lock-free event queue
    /// Python should get the queue handle via get_event_queue_handle()
    /// This prevents GIL deadlock during file copy operations

    /// Get event queue handle for Python event pump
    pub fn get_event_queue(&self) -> Arc<crate::event_queue::EventQueue> {
        if let Ok(event_system) = self.event_system.lock() {
            event_system.get_queue()
        } else {
            // Fallback: create temporary queue (should never happen)
            Arc::new(crate::event_queue::EventQueue::with_default_capacity())
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
        let bytes = self
            .total_bytes_transferred
            .load(std::sync::atomic::Ordering::Relaxed) as u64;
        let files = self
            .total_files_processed
            .load(std::sync::atomic::Ordering::Relaxed) as usize;
        let elapsed = (now_secs() - start_time).max(0.0);
        let speed_mib_s = if elapsed > 0.0 {
            (bytes as f64 / elapsed) / (1024.0 * 1024.0)
        } else {
            0.0
        };

        // NOTE: use MiB/s (not Mb/s)
        let _ = event_system.emit_job_progress(
            bytes,
            total_bytes,
            files,
            total_files,
            elapsed,
            speed_mib_s,
        );
    }

    /// Main method to copy files
    pub fn copy_files(&self, job: &CopyJob) -> Result<CopyStats> {
        // DEBUG: Log at the very start to verify this code path executes
        let _ = std::fs::write("/tmp/rust_engine_debug.log",
            format!("🚀 ENGINE START: copy_files() called for job: {}\n", job.job_id));

        let start_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64();

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
        let total_bytes: u64 = source_files
            .iter()
            .filter_map(|p| get_file_size(p).ok())
            .sum();

        // Update progress tracker with initial values
        if let Ok(tracker) = self.progress_tracker.lock() {
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

        let relative_paths = self.compute_relative_paths(job, &source_files);

        // CRITICAL FIX: Always use MultiDestCopyEngine regardless of destination count
        // This ensures consistent event emission, progress tracking, and DIT report generation
        // whether transferring to 1, 2, or 10 destinations
        let file_records = self.copy_to_multiple_destinations(
            job,
            &source_files,
            &relative_paths,
            start_time,
            total_bytes,
            total_files,
        )?;

        copy_stats.end_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64();
        copy_stats.copied_files = self
            .total_files_processed
            .load(std::sync::atomic::Ordering::Relaxed) as usize;
        copy_stats.copied_bytes = self
            .total_bytes_transferred
            .load(std::sync::atomic::Ordering::Relaxed);

        // Add file records to copy stats
        copy_stats.files = file_records;

        // Calculate speeds
        let duration = copy_stats.end_time - copy_stats.start_time;
        if duration > 0.0 {
            copy_stats.speed_mib_s =
                (copy_stats.copied_bytes as f64 / duration) / (1024.0 * 1024.0);
            copy_stats.data_mib_s = copy_stats.speed_mib_s;
            copy_stats.data_elapsed_s = duration;
        }

        // Clear current job ID
        if let Ok(mut current_job) = self.current_job_id.lock() {
            *current_job = None;
        }

        Ok(copy_stats)
    }

    fn compute_relative_paths(
        &self,
        job: &CopyJob,
        source_files: &[std::path::PathBuf],
    ) -> Vec<std::path::PathBuf> {
        source_files
            .iter()
            .map(|path| {
                for source_root in &job.source_paths {
                    let root = std::path::Path::new(source_root);
                    if let Ok(rel) = path.strip_prefix(root) {
                        return rel.to_path_buf();
                    }
                }

                path.file_name()
                    .map(|name| std::path::PathBuf::from(name.to_string_lossy().to_string()))
                    .unwrap_or_else(|| path.to_path_buf())
            })
            .collect()
    }


    /// Copy files to multiple destinations
    fn copy_to_multiple_destinations(
        &self,
        job: &CopyJob,
        source_files: &[std::path::PathBuf],
        relative_paths: &[std::path::PathBuf],
        start_time: f64,
        total_bytes: u64,
        total_files: usize,
    ) -> Result<Vec<FileTransferRecord>> {
        let mut file_records = Vec::new();
        let dest_count = job.destination_paths.len();

        if dest_count == 0 {
            return Ok(file_records);
        }

        let total_target_bytes = total_bytes.saturating_mul(dest_count as u64);
        let hash_algorithm = if job.verify_integrity {
            HashAlgorithm::from_string(&job.hash_algorithm)
        } else {
            HashAlgorithm::XxHash64
        };
        let hash_name = hash_algorithm.to_string();

        let chunk_size = if job.block_size == 0 {
            None
        } else {
            Some(job.block_size)
        };

        let multi_engine = MultiDestCopyEngine::new(Arc::clone(&self.cancelled), chunk_size);

        let file_sizes: Vec<u64> = source_files
            .iter()
            .map(|path| get_file_size(path).unwrap_or(0))
            .collect();

        let mut file_bytes_progress = vec![0u64; total_files];
        let mut file_completed = vec![false; total_files];
        let mut dest_bytes_progress = vec![0u64; dest_count];
        let mut dest_files_completed = vec![0usize; dest_count];
        let mut job_bytes_copied: u64 = 0;
        let mut job_files_completed: usize = 0;
        let progress_start = now_secs();

        let cancelled = Arc::clone(&self.cancelled);
        let event_system = Arc::clone(&self.event_system);

        let outcomes = multi_engine.copy(
            source_files,
            relative_paths,
            &job.destination_paths,
            hash_algorithm.clone(),
            Arc::clone(&self.event_system),
            |progress| {
                if cancelled.load(Ordering::Relaxed) {
                    return true;
                }

                let chunk_bytes = progress.chunk_bytes;
                let file_index = progress.file_index;

                if file_index < file_bytes_progress.len() {
                    file_bytes_progress[file_index] =
                        file_bytes_progress[file_index].saturating_add(chunk_bytes);
                    if !file_completed[file_index]
                        && file_bytes_progress[file_index] >= file_sizes[file_index]
                    {
                        file_completed[file_index] = true;
                        for dest_idx in 0..dest_count {
                            dest_files_completed[dest_idx] += 1;
                        }
                        job_files_completed = job_files_completed.saturating_add(dest_count);
                        self.total_files_processed
                            .fetch_add(dest_count as u64, Ordering::Relaxed);

                        // NOTE: File completion events with hashes will be emitted later
                        // after the entire batch completes and hashes are computed
                        // See lines ~796-822 for the proper emission with hash values
                    }
                }

                let delta = chunk_bytes.saturating_mul(dest_count as u64);
                job_bytes_copied = job_bytes_copied.saturating_add(delta);
                self.total_bytes_transferred
                    .fetch_add(delta, Ordering::Relaxed);

                for dest_idx in 0..dest_count {
                    dest_bytes_progress[dest_idx] =
                        dest_bytes_progress[dest_idx].saturating_add(chunk_bytes);
                }

                if let Ok(event_system) = event_system.lock() {
                    let elapsed = (now_secs() - progress_start).max(0.0);
                    let speed_mib_s = if elapsed > 0.0 {
                        (job_bytes_copied as f64 / elapsed) / (1024.0 * 1024.0)
                    } else {
                        0.0
                    };

                    let _ = event_system.emit_job_progress(
                        job_bytes_copied,
                        total_target_bytes,
                        job_files_completed,
                        total_files * dest_count,
                        elapsed,
                        speed_mib_s,
                    );

                    for (dest_idx, dest_path) in job.destination_paths.iter().enumerate() {
                        let mut dest_progress = DestProgressPayload::default();
                        dest_progress.dest_index = dest_idx;
                        dest_progress.dest_path = dest_path.clone();
                        dest_progress.transfer_type = "COPY".to_string();
                        dest_progress.bytes_copied = dest_bytes_progress[dest_idx];
                        dest_progress.total_bytes = total_bytes;
                        dest_progress.completed_files = dest_files_completed[dest_idx];
                        dest_progress.total_files = total_files;
                        dest_progress.current_speed_mib_s = speed_mib_s;
                        dest_progress.peak_speed_mib_s = speed_mib_s;
                        dest_progress.elapsed_time = elapsed;
                        let _ = event_system.emit_dest_progress(&dest_progress);
                    }
                }

                false
            },
        )?;

        // DEBUG: Log after multi_engine.copy() returns
        let _ = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open("/tmp/rust_engine_debug.log")
            .and_then(|mut f| std::io::Write::write_all(&mut f,
                format!("✅ multi_engine.copy() returned {} outcomes\n", outcomes.len()).as_bytes()));

        let mut dest_bytes = vec![0u64; dest_count];
        let mut dest_files = vec![0usize; dest_count];

        // CRITICAL: Process all completed outcomes even if cancelled
        // This ensures file.complete events with hashes are emitted for files that finished

        // DEBUG: Log to file since eprintln() is swallowed by GUI
        let _ = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open("/tmp/rust_engine_debug.log")
            .and_then(|mut f| std::io::Write::write_all(&mut f,
                format!("🔄 ENGINE_CORE: About to process {} outcomes\n", outcomes.len()).as_bytes()));

        for outcome in outcomes {
            let source_path_str = outcome.source_path.to_string_lossy().to_string();
            let source_hash = outcome.source_hash.clone();

            for dest in outcome.destinations {
                let relative_path = if dest.relative_path.as_os_str().is_empty() {
                    outcome.relative_path.clone()
                } else {
                    dest.relative_path.clone()
                };

                let full_dest_path = std::path::Path::new(&dest.dest_path).join(&relative_path);
                let dest_path_str = full_dest_path.to_string_lossy().to_string();
                let filename = relative_path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .unwrap_or("unknown")
                    .to_string();

                let duration_secs = if dest.duration_ms > 0 {
                    dest.duration_ms as f64 / 1000.0
                } else {
                    0.0
                };

                let transfer_speed_mib_s = if duration_secs > 0.0 && dest.bytes_written > 0 {
                    (dest.bytes_written as f64 / duration_secs) / (1024.0 * 1024.0)
                } else {
                    0.0
                };

                let mut record = FileTransferRecord::default();
                record.filename = filename.clone();
                record.source_path = source_path_str.clone();
                record.destination_path = dest_path_str.clone();
                record.file_size = dest.bytes_written;
                record.transfer_speed_mib_s = transfer_speed_mib_s;

                if let Some(error) = dest.error {
                    record.status = "FAILED".to_string();
                    record.error_message = error.clone();
                    record.verification_passed = false;
                    record.verification_error = error;

                    if let Ok(event_system) = self.event_system.lock() {
                        let _ = event_system.emit_event(
                            "file.error",
                            Python::with_gil(|py| {
                                let payload = pyo3::types::PyDict::new(py);
                                let _ = payload.set_item("filename", &record.filename);
                                let _ = payload.set_item("source_path", &record.source_path);
                                let _ = payload.set_item("dest_path", &record.destination_path);
                                let _ = payload.set_item("error", &record.error_message);
                                payload.into_py(py)
                            }),
                        );
                    }

                    file_records.push(record);
                    continue;
                }

                let dest_hash = dest.dest_hash.unwrap_or_default();
                record.checksum_source = source_hash.clone();
                record.checksum_destination = dest_hash.clone();

                let verification_passed =
                    !source_hash.is_empty() && !dest_hash.is_empty() && source_hash == dest_hash;

                record.verification_passed = verification_passed;
                if verification_passed {
                    record.status = "COMPLETED".to_string();
                    record.verification_error.clear();
                } else {
                    record.status = "VERIFICATION_FAILED".to_string();
                    record.verification_error = "Checksum mismatch".to_string();
                }

                dest_bytes[dest.dest_index] =
                    dest_bytes[dest.dest_index].saturating_add(dest.bytes_written);
                dest_files[dest.dest_index] += 1;

                if let Ok(tracker) = self.progress_tracker.lock() {
                    tracker.add_file_record(record.clone());
                    tracker.update_overall_progress(
                        self.total_bytes_transferred.load(Ordering::Relaxed),
                        self.total_files_processed.load(Ordering::Relaxed) as usize,
                    );
                }

                // DEBUG: Append to log file
                let _ = std::fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open("/tmp/rust_engine_debug.log")
                    .and_then(|mut f| std::io::Write::write_all(&mut f,
                        format!("🔥 About to emit FileCompleted for: {}\n", record.filename).as_bytes()));

                if let Ok(event_system) = self.event_system.lock() {

                    let mut dest_progress = DestProgressPayload::default();
                    dest_progress.dest_index = dest.dest_index;
                    dest_progress.dest_path = dest.dest_path.clone();
                    dest_progress.transfer_type = "COPY".to_string();
                    dest_progress.bytes_copied = dest_bytes[dest.dest_index];
                    dest_progress.total_bytes = total_bytes;
                    dest_progress.completed_files = dest_files[dest.dest_index];
                    dest_progress.total_files = total_files;
                    dest_progress.current_speed_mib_s = transfer_speed_mib_s;
                    dest_progress.peak_speed_mib_s = transfer_speed_mib_s;
                    dest_progress.elapsed_time = duration_secs;

                    let _ = event_system.emit_dest_progress(&dest_progress);

                    let _ = event_system.emit_file_completed_with_hash(
                        &record.filename,
                        &source_path_str,
                        &dest_path_str,
                        dest.dest_index,
                        dest.bytes_written,
                        &source_hash,
                        &dest_hash,
                        &hash_name,
                        verification_passed,
                    );

                    // DEBUG: Log successful emission
                    let _ = std::fs::OpenOptions::new()
                        .create(true)
                        .append(true)
                        .open("/tmp/rust_engine_debug.log")
                        .and_then(|mut f| std::io::Write::write_all(&mut f,
                            format!("✅ FileCompleted emitted for: {} (hash: {})\n", record.filename, source_hash).as_bytes()));

                    self.emit_job_progress_locked(
                        &event_system,
                        start_time,
                        total_target_bytes,
                        total_files * dest_count,
                    );
                } else {
                    eprintln!("❌❌❌ ENGINE_CORE: FAILED TO LOCK event_system for file: {}", record.filename);
                }

                file_records.push(record);
            }
        }

        if let Ok(event_system) = self.event_system.lock() {
            for (dest_index, dest_path) in job.destination_paths.iter().enumerate() {
                let mut dest_completion = DestProgressPayload::default();
                dest_completion.dest_index = dest_index;
                dest_completion.dest_path = dest_path.clone();
                dest_completion.transfer_type = "COPY".to_string();
                dest_completion.completed_files = dest_files[dest_index];
                dest_completion.total_files = total_files;
                dest_completion.bytes_copied = dest_bytes[dest_index];
                dest_completion.total_bytes = total_bytes;

                let _ = event_system.emit_dest_progress(&dest_completion);
                let elapsed = (now_secs() - start_time).max(0.0);
                let _ = event_system.emit_dest_completed(
                    dest_index,
                    dest_path,
                    dest_bytes[dest_index],
                    total_bytes,
                    dest_files[dest_index],
                    total_files,
                    elapsed,
                );

                debug!(dest = %dest_path, index = dest_index, "Emitted destination completion");
            }
        }

        Ok(file_records)
    }

    /// Cancel the current operation
    pub fn cancel(&self) {
        self.cancelled
            .store(true, std::sync::atomic::Ordering::Relaxed);

        // Emit cancellation event
        if let Ok(event_system) = self.event_system.lock() {
            let _ = event_system.emit_event("cancelled", Python::with_gil(|py| py.None()));
        }
    }

    /// Pause the current operation
    pub fn pause(&self) {
        self.paused
            .store(true, std::sync::atomic::Ordering::Relaxed);

        // Emit pause event
        if let Ok(event_system) = self.event_system.lock() {
            let _ = event_system.emit_event("paused", Python::with_gil(|py| py.None()));
        }
    }

    /// Resume the current operation
    pub fn resume(&self) {
        self.paused
            .store(false, std::sync::atomic::Ordering::Relaxed);

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


    /// Check if operation is paused
    pub fn is_paused(&self) -> bool {
        self.paused.load(std::sync::atomic::Ordering::Relaxed)
    }

    /// Reset engine state
    pub fn reset(&self) {
        self.cancelled
            .store(false, std::sync::atomic::Ordering::Relaxed);
        self.paused
            .store(false, std::sync::atomic::Ordering::Relaxed);
        self.total_files_processed
            .store(0, std::sync::atomic::Ordering::Relaxed);
        self.total_bytes_transferred
            .store(0, std::sync::atomic::Ordering::Relaxed);

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

    /// REMOVED: set_event_sink - causes GIL deadlock
    /// Use get_event_queue_handle() instead and create Python event pump thread

    /// Get event queue handle for Python event pump
    fn get_event_queue_handle(&self) -> crate::event_system::PyEventQueueHandle {
        // Get the event system and its queue handle
        if let Ok(event_system) = self.inner.event_system.lock() {
            crate::event_system::PyEventQueueHandle::new(event_system.get_queue())
        } else {
            // Fallback: create a temporary queue handle
            use crate::event_queue::EventQueue;
            crate::event_system::PyEventQueueHandle::new(
                std::sync::Arc::new(EventQueue::with_default_capacity())
            )
        }
    }

    fn copy_files(&self, py: Python, job: &CopyJob) -> PyResult<CopyStats> {
        // Release the GIL during the file copy operation to allow UI updates
        py.allow_threads(|| {
            match self.inner.copy_files(job) {
                Ok(stats) => Ok(stats),
                Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
            }
        })
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

    fn emit_job_progress(
        &self,
        bytes_copied: u64,
        total_bytes: u64,
        files_completed: usize,
        total_files: usize,
        elapsed: f64,
        speed_mib_s: f64,
    ) -> PyResult<()> {
        self.inner.emit_job_progress(
            bytes_copied,
            total_bytes,
            files_completed,
            total_files,
            elapsed,
            speed_mib_s,
        )
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
