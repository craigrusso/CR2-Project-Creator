//! Event system for GIL-free Rust → Python communication
//!
//! This module provides event emission using a lock-free queue instead of Python callbacks.
//! NO Python::with_gil() calls during file copy = NO GIL DEADLOCK

use crate::data_structures::{DestProgressPayload, FileTransferRecord, JobManifest, JobStats};
use crate::event_queue::{EventQueue, TransferEvent};
use pyo3::prelude::*;
use std::sync::Arc;

/// Event system for managing transfer events without GIL contention
pub struct EventSystem {
    event_queue: Arc<EventQueue>,
}

impl EventSystem {
    /// Create a new event system with lock-free queue
    pub fn new() -> Self {
        Self {
            event_queue: Arc::new(EventQueue::with_default_capacity()),
        }
    }

    /// Get a reference to the event queue (for sharing with other threads)
    pub fn get_queue(&self) -> Arc<EventQueue> {
        Arc::clone(&self.event_queue)
    }

    /// Emit destination progress event (NO GIL NEEDED)
    pub fn emit_dest_progress(&self, payload: &DestProgressPayload) -> PyResult<()> {
        let event = TransferEvent::DestProgress {
            dest_index: payload.dest_index,
            dest_path: payload.dest_path.clone(),
            transfer_type: payload.transfer_type.clone(),
            bytes_copied: payload.bytes_copied,
            total_bytes: payload.total_bytes,
            current_speed_mbps: payload.current_speed_mib_s,
            peak_speed_mbps: payload.peak_speed_mib_s,
            elapsed_time: payload.elapsed_time,
            completed_files: payload.completed_files,
            total_files: payload.total_files,
            progress_percent: if payload.total_bytes > 0 {
                (payload.bytes_copied as f64 / payload.total_bytes as f64) * 100.0
            } else {
                0.0
            },
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit job.start event with JobManifest (NO GIL NEEDED)
    pub fn emit_job_start(&self, manifest: &JobManifest, destinations: &[String]) -> PyResult<()> {
        let event = TransferEvent::JobStarted {
            job_id: manifest.job_id.clone(),
            total_files: manifest.total_files as usize,
            total_bytes: manifest.total_bytes as u64,
            destinations: destinations.to_vec(),
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit job.progress event with JobStats (NO GIL NEEDED)
    pub fn emit_job_progress_stats(&self, stats: &JobStats) -> PyResult<()> {
        let event = TransferEvent::JobProgress {
            job_id: stats.job_id.clone(),
            bytes_copied: stats.bytes_copied as u64,
            total_bytes: stats.total_target_bytes as u64,
            files_completed: stats.completed_files as usize,
            total_files: stats.total_files as usize,
            elapsed_s: stats.elapsed_seconds,
            speed_mbps: stats.current_speed_mbps,
            current_speed_mbps: stats.current_speed_mbps,
            peak_speed_mbps: stats.peak_speed_mbps,
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit job progress event (legacy compatibility) (NO GIL NEEDED)
    pub fn emit_job_progress(
        &self,
        bytes_copied: u64,
        total_bytes: u64,
        files_completed: usize,
        total_files: usize,
        elapsed_s: f64,
        speed_mib_s: f64,
    ) -> PyResult<()> {
        let event = TransferEvent::JobProgress {
            job_id: "unknown".to_string(),
            bytes_copied,
            total_bytes,
            files_completed,
            total_files,
            elapsed_s,
            speed_mbps: speed_mib_s,
            current_speed_mbps: speed_mib_s,
            peak_speed_mbps: speed_mib_s,
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit file completed event with comprehensive data including hash (NO GIL NEEDED)
    pub fn emit_file_completed_with_hash(
        &self,
        filename: &str,
        source_path: &str,
        dest_path: &str,
        bytes: u64,
        source_hash: &str,
        dest_hash: &str,
    ) -> PyResult<()> {
        let event = TransferEvent::FileCompleted {
            filename: filename.to_string(),
            source_path: source_path.to_string(),
            dest_path: dest_path.to_string(),
            bytes_copied: bytes,
            source_checksum: source_hash.to_string(),
            dest_checksum: dest_hash.to_string(),
            verification_passed: source_hash == dest_hash,
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit file completed event (legacy compatibility) (NO GIL NEEDED)
    pub fn emit_file_completed(&self, filename: &str, bytes: u64) -> PyResult<()> {
        let event = TransferEvent::FileCompleted {
            filename: filename.to_string(),
            source_path: String::new(),
            dest_path: String::new(),
            bytes_copied: bytes,
            source_checksum: String::new(),
            dest_checksum: String::new(),
            verification_passed: true,
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit file started event (NO GIL NEEDED)
    pub fn emit_file_started(
        &self,
        file_id: &str,
        filename: &str,
        total_bytes: u64,
    ) -> PyResult<()> {
        let event = TransferEvent::FileStarted {
            file_id: file_id.to_string(),
            filename: filename.to_string(),
            source_path: String::new(),
            dest_path: String::new(),
            total_bytes,
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit file.progress event with proper schema (NO GIL NEEDED)
    pub fn emit_file_progress_new(
        &self,
        _job_id: &str,
        filename: &str,
        file_bytes: u64,
        file_bytes_copied: u64,
        _dest_index: usize,
        _transfer_state: &str,
    ) -> PyResult<()> {
        let event = TransferEvent::FileProgress {
            filename: filename.to_string(),
            bytes_copied: file_bytes_copied,
            total_bytes: file_bytes,
            speed_mbps: 0.0, // Will be calculated by Python side
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit verification event (NO GIL NEEDED)
    pub fn emit_verification_event(&self, record: &FileTransferRecord) -> PyResult<()> {
        let event = TransferEvent::FileCompleted {
            filename: record.filename.clone(),
            source_path: record.source_path.clone(),
            dest_path: record.destination_path.clone(),
            bytes_copied: record.file_size,
            source_checksum: record.checksum_source.clone(),
            dest_checksum: record.checksum_destination.clone(),
            verification_passed: record.verification_passed,
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Emit error event (NO GIL NEEDED)
    pub fn emit_error_event(&self, error_message: &str, context: Option<&str>) -> PyResult<()> {
        let event = TransferEvent::Error {
            message: error_message.to_string(),
            context: context.map(|s| s.to_string()),
        };

        self.event_queue
            .send(event)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Legacy emit_event method - DEPRECATED, does nothing
    /// Old code calls this with Python::with_gil() which causes GIL deadlock
    /// Just ignore these calls - proper typed methods above handle events correctly
    pub fn emit_event(&self, _event_type: &str, _payload: PyObject) {
        // INTENTIONALLY EMPTY - prevents GIL deadlock from old code paths
        // All events now go through typed methods which use lock-free queue
    }
}

impl Default for EventSystem {
    fn default() -> Self {
        Self::new()
    }
}

/// Python wrapper for EventSystem (provides queue access to Python)
#[pyclass]
pub struct PyEventSystem {
    inner: Arc<EventSystem>,
}

#[pymethods]
impl PyEventSystem {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(EventSystem::new()),
        }
    }

    /// Get event queue handle for Python event pump
    fn get_queue_handle(&self) -> PyEventQueueHandle {
        PyEventQueueHandle {
            queue: self.inner.get_queue(),
        }
    }
}

/// Python-accessible event queue handle for event pump thread
#[pyclass]
pub struct PyEventQueueHandle {
    queue: Arc<EventQueue>,
}

impl PyEventQueueHandle {
    /// Create a new handle from an event queue
    pub fn new(queue: Arc<EventQueue>) -> Self {
        Self { queue }
    }
}

#[pymethods]
impl PyEventQueueHandle {
    /// Try to receive a single event (returns None if queue is empty)
    fn try_recv_event(&self) -> Option<String> {
        self.queue.try_recv().map(|event| {
            // Serialize event to JSON for Python
            serde_json::to_string(&event).unwrap_or_else(|_| "{}".to_string())
        })
    }

    /// Drain all pending events (returns list of JSON strings)
    fn drain_all_events(&self) -> Vec<String> {
        self.queue
            .drain_all()
            .into_iter()
            .filter_map(|event| serde_json::to_string(&event).ok())
            .collect()
    }

    /// Get approximate number of events in queue
    fn len(&self) -> usize {
        self.queue.len()
    }

    /// Check if queue is empty
    fn is_empty(&self) -> bool {
        self.queue.is_empty()
    }
}

/// Register Python types for this module
pub fn register_python_types(m: &PyModule) -> PyResult<()> {
    m.add_class::<PyEventSystem>()?;
    m.add_class::<PyEventQueueHandle>()?;
    Ok(())
}
