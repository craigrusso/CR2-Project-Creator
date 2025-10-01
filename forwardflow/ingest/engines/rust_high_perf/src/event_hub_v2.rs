//! ForwardFlow V2.0 - Professional EventHub Implementation in Rust
//!
//! High-performance, multi-threaded event distribution system designed for
//! professional DIT workflows. Uses Rust's advanced concurrency features
//! for maximum performance and memory safety.

use anyhow::Result;
use crossbeam_channel::{bounded, unbounded, Receiver, Sender};
use dashmap::DashMap;
use parking_lot::{Mutex, RwLock};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::sync::{
    atomic::{AtomicBool, AtomicU64, Ordering},
    Arc,
};
use std::thread::{self, JoinHandle};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

/// Event types for the professional DIT system
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EventType {
    // File-level events
    FileStarted,
    FileProgress,
    FileCompleted,
    FileError,
    FileHashCalculated,

    // Destination-level events
    DestStarted,
    DestProgress,
    DestCompleted,
    DestError,

    // Job-level events
    JobStarted,
    JobProgress,
    JobCompleted,
    JobCancelled,
    JobError,
    JobStrategySelected,

    // BLAST workflow events
    BlastInitiated,
    BlastCompleted,
    BlastDistributionStarted,
    BlastDistributionCompleted,

    // System events
    SystemResumeAvailable,
    SystemCheckpointSaved,
}

/// Event priority for processing order
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EventPriority {
    Critical = 1, // BLAST completion, errors
    High = 2,     // File completion, destination completion
    Normal = 3,   // Progress updates
    Low = 4,      // Status changes
}

/// Core event structure with comprehensive metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransferEvent {
    pub event_type: EventType,
    pub priority: EventPriority,
    pub timestamp_ns: u64, // Nanosecond precision
    pub job_id: String,
    pub payload: EventPayload,
}

/// Event payload variants for different event types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EventPayload {
    File {
        file_id: String,
        filename: String,
        file_size: u64,
        bytes_copied: u64,
        destination_path: String,
        source_checksum: Option<String>,
        destination_checksum: Option<String>,
        hash_algorithm: String,
        transfer_speed_mbps: f64,
        error_message: Option<String>,
    },
    Destination {
        destination_path: String,
        destination_index: usize,
        progress_percent: f64,
        bytes_copied: u64,
        total_bytes: u64,
        completed_files: usize,
        total_files: usize,
        current_speed_mbps: f64,
        peak_speed_mbps: f64,
        eta_seconds: f64,
        error_message: Option<String>,
    },
    Job {
        total_destinations: usize,
        completed_destinations: usize,
        total_speed_mbps: f64, // Sum of all destination speeds
        peak_speed_mbps: f64,
        progress_percent: f64, // Based on slowest destination
        eta_seconds: f64,
        total_bytes: u64,
        copied_bytes: u64,
        total_files: usize,
        completed_files: usize,
        strategy_name: String,
        error_message: Option<String>,
    },
    Blast {
        blast_drive_path: String,
        distribution_destinations: Vec<String>,
        blast_progress_percent: f64,
        distribution_progress_percent: f64,
        phase: String,
    },
    System {
        message: String,
        data: serde_json::Value,
    },
}

impl TransferEvent {
    pub fn new(
        event_type: EventType,
        priority: EventPriority,
        job_id: String,
        payload: EventPayload,
    ) -> Self {
        Self {
            event_type,
            priority,
            timestamp_ns: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_nanos() as u64,
            job_id,
            payload,
        }
    }
}

/// Statistics for monitoring event processing performance
#[derive(Debug, Default)]
pub struct EventStats {
    pub events_processed: AtomicU64,
    pub events_dropped: AtomicU64,
    pub avg_processing_time_ns: AtomicU64,
    pub peak_processing_time_ns: AtomicU64,
    pub events_by_type: DashMap<EventType, u64>,
}

impl EventStats {
    pub fn record_event(&self, event_type: EventType, processing_time_ns: u64) {
        self.events_processed.fetch_add(1, Ordering::Relaxed);

        // Update average processing time (simple rolling average)
        let current_avg = self.avg_processing_time_ns.load(Ordering::Relaxed);
        let processed = self.events_processed.load(Ordering::Relaxed);
        let new_avg = if processed == 1 {
            processing_time_ns
        } else {
            (current_avg * (processed - 1) + processing_time_ns) / processed
        };
        self.avg_processing_time_ns
            .store(new_avg, Ordering::Relaxed);

        // Update peak processing time
        let current_peak = self.peak_processing_time_ns.load(Ordering::Relaxed);
        if processing_time_ns > current_peak {
            self.peak_processing_time_ns
                .store(processing_time_ns, Ordering::Relaxed);
        }

        // Update event type counter
        *self.events_by_type.entry(event_type).or_insert(0) += 1;
    }

    pub fn record_dropped_event(&self) {
        self.events_dropped.fetch_add(1, Ordering::Relaxed);
    }
}

/// Specialized event handler trait for different event types
pub trait EventHandler: Send + Sync {
    fn handle_event(&self, event: &TransferEvent) -> Result<()>;
    fn handler_name(&self) -> &'static str;
}

/// High-performance, multi-threaded event distribution hub
pub struct EventHub {
    // Event channels for different handler threads
    file_sender: Sender<TransferEvent>,
    dest_sender: Sender<TransferEvent>,
    job_sender: Sender<TransferEvent>,
    blast_sender: Sender<TransferEvent>,

    // Handler threads
    handler_threads: Vec<JoinHandle<()>>,

    // Event handlers
    file_handlers: Arc<RwLock<Vec<Arc<dyn EventHandler>>>>,
    dest_handlers: Arc<RwLock<Vec<Arc<dyn EventHandler>>>>,
    job_handlers: Arc<RwLock<Vec<Arc<dyn EventHandler>>>>,
    blast_handlers: Arc<RwLock<Vec<Arc<dyn EventHandler>>>>,

    // Performance monitoring
    stats: Arc<EventStats>,

    // Shutdown coordination
    shutdown_signal: Arc<AtomicBool>,
}

impl EventHub {
    /// Create a new high-performance EventHub
    pub fn new() -> Result<Self> {
        let (file_sender, file_receiver) = bounded(50_000); // Large buffer for file events
        let (dest_sender, dest_receiver) = bounded(10_000);
        let (job_sender, job_receiver) = bounded(5_000);
        let (blast_sender, blast_receiver) = bounded(1_000);

        let file_handlers = Arc::new(RwLock::new(Vec::new()));
        let dest_handlers = Arc::new(RwLock::new(Vec::new()));
        let job_handlers = Arc::new(RwLock::new(Vec::new()));
        let blast_handlers = Arc::new(RwLock::new(Vec::new()));

        let stats = Arc::new(EventStats::default());
        let shutdown_signal = Arc::new(AtomicBool::new(false));

        let mut handler_threads = Vec::new();

        // Spawn specialized handler threads
        handler_threads.push(Self::spawn_handler_thread(
            "FileEventHandler",
            file_receiver,
            file_handlers.clone(),
            stats.clone(),
            shutdown_signal.clone(),
        ));

        handler_threads.push(Self::spawn_handler_thread(
            "DestEventHandler",
            dest_receiver,
            dest_handlers.clone(),
            stats.clone(),
            shutdown_signal.clone(),
        ));

        handler_threads.push(Self::spawn_handler_thread(
            "JobEventHandler",
            job_receiver,
            job_handlers.clone(),
            stats.clone(),
            shutdown_signal.clone(),
        ));

        handler_threads.push(Self::spawn_handler_thread(
            "BlastEventHandler",
            blast_receiver,
            blast_handlers.clone(),
            stats.clone(),
            shutdown_signal.clone(),
        ));

        println!(
            "EventHub V2.0 initialized with {} handler threads",
            handler_threads.len()
        );

        Ok(Self {
            file_sender,
            dest_sender,
            job_sender,
            blast_sender,
            handler_threads,
            file_handlers,
            dest_handlers,
            job_handlers,
            blast_handlers,
            stats,
            shutdown_signal,
        })
    }

    /// Emit an event to the appropriate handler thread
    pub fn emit_event(&self, event: TransferEvent) -> Result<()> {
        let sender = match event.event_type {
            EventType::FileStarted
            | EventType::FileProgress
            | EventType::FileCompleted
            | EventType::FileError
            | EventType::FileHashCalculated => &self.file_sender,

            EventType::DestStarted
            | EventType::DestProgress
            | EventType::DestCompleted
            | EventType::DestError => &self.dest_sender,

            EventType::JobStarted
            | EventType::JobProgress
            | EventType::JobCompleted
            | EventType::JobCancelled
            | EventType::JobError
            | EventType::JobStrategySelected => &self.job_sender,

            EventType::BlastInitiated
            | EventType::BlastCompleted
            | EventType::BlastDistributionStarted
            | EventType::BlastDistributionCompleted => &self.blast_sender,

            EventType::SystemResumeAvailable | EventType::SystemCheckpointSaved => &self.job_sender,
        };

        match sender.try_send(event) {
            Ok(()) => Ok(()),
            Err(_) => {
                self.stats.record_dropped_event();
                anyhow::bail!("Event queue full, dropping event")
            }
        }
    }

    /// Register a handler for file events
    pub fn register_file_handler(&self, handler: Arc<dyn EventHandler>) {
        self.file_handlers.write().push(handler);
    }

    /// Register a handler for destination events
    pub fn register_dest_handler(&self, handler: Arc<dyn EventHandler>) {
        self.dest_handlers.write().push(handler);
    }

    /// Register a handler for job events
    pub fn register_job_handler(&self, handler: Arc<dyn EventHandler>) {
        self.job_handlers.write().push(handler);
    }

    /// Register a handler for BLAST events
    pub fn register_blast_handler(&self, handler: Arc<dyn EventHandler>) {
        self.blast_handlers.write().push(handler);
    }

    /// Get comprehensive performance statistics
    pub fn get_stats(&self) -> EventHubStats {
        EventHubStats {
            events_processed: self.stats.events_processed.load(Ordering::Relaxed),
            events_dropped: self.stats.events_dropped.load(Ordering::Relaxed),
            avg_processing_time_ns: self.stats.avg_processing_time_ns.load(Ordering::Relaxed),
            peak_processing_time_ns: self.stats.peak_processing_time_ns.load(Ordering::Relaxed),
            events_by_type: self
                .stats
                .events_by_type
                .iter()
                .map(|entry| (entry.key().clone(), *entry.value()))
                .collect(),
            active_threads: self.handler_threads.len(),
        }
    }

    /// Graceful shutdown of all handler threads
    pub fn shutdown(&mut self) -> Result<()> {
        println!("Shutting down EventHub V2.0...");

        self.shutdown_signal.store(true, Ordering::Relaxed);

        // Wait for all threads to complete
        while let Some(handle) = self.handler_threads.pop() {
            if let Err(e) = handle.join() {
                eprintln!("Handler thread panicked: {:?}", e);
            }
        }

        println!("EventHub V2.0 shutdown complete");
        Ok(())
    }

    /// Spawn a specialized handler thread
    fn spawn_handler_thread(
        name: &'static str,
        receiver: Receiver<TransferEvent>,
        handlers: Arc<RwLock<Vec<Arc<dyn EventHandler>>>>,
        stats: Arc<EventStats>,
        shutdown_signal: Arc<AtomicBool>,
    ) -> JoinHandle<()> {
        thread::Builder::new()
            .name(name.to_string())
            .spawn(move || {
                println!("Started {} thread", name);

                while !shutdown_signal.load(Ordering::Relaxed) {
                    match receiver.recv_timeout(Duration::from_millis(100)) {
                        Ok(event) => {
                            let start_time = SystemTime::now();

                            // Process event with all registered handlers
                            let handlers_guard = handlers.read();
                            for handler in handlers_guard.iter() {
                                if let Err(e) = handler.handle_event(&event) {
                                    eprintln!("Handler {} error: {}", handler.handler_name(), e);
                                }
                            }

                            // Record processing statistics
                            if let Ok(duration) = start_time.elapsed() {
                                stats.record_event(event.event_type, duration.as_nanos() as u64);
                            }
                        }
                        Err(crossbeam_channel::RecvTimeoutError::Timeout) => continue,
                        Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
                    }
                }

                println!("{} thread shutting down", name);
            })
            .expect("Failed to spawn handler thread")
    }
}

/// Statistics structure for external monitoring
#[derive(Debug, Clone)]
pub struct EventHubStats {
    pub events_processed: u64,
    pub events_dropped: u64,
    pub avg_processing_time_ns: u64,
    pub peak_processing_time_ns: u64,
    pub events_by_type: Vec<(EventType, u64)>,
    pub active_threads: usize,
}

impl Drop for EventHub {
    fn drop(&mut self) {
        if !self.shutdown_signal.load(Ordering::Relaxed) {
            let _ = self.shutdown();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicUsize;

    struct TestHandler {
        name: &'static str,
        events_received: AtomicUsize,
    }

    impl TestHandler {
        fn new(name: &'static str) -> Arc<Self> {
            Arc::new(Self {
                name,
                events_received: AtomicUsize::new(0),
            })
        }
    }

    impl EventHandler for TestHandler {
        fn handle_event(&self, _event: &TransferEvent) -> Result<()> {
            self.events_received.fetch_add(1, Ordering::Relaxed);
            Ok(())
        }

        fn handler_name(&self) -> &'static str {
            self.name
        }
    }

    #[test]
    fn test_event_hub_creation() {
        let hub = EventHub::new().expect("Failed to create EventHub");
        assert_eq!(hub.handler_threads.len(), 4);
    }

    #[test]
    fn test_event_routing() {
        let mut hub = EventHub::new().expect("Failed to create EventHub");

        let file_handler = TestHandler::new("FileTestHandler");
        let dest_handler = TestHandler::new("DestTestHandler");

        hub.register_file_handler(file_handler.clone());
        hub.register_dest_handler(dest_handler.clone());

        // Test file event
        let file_event = TransferEvent::new(
            EventType::FileStarted,
            EventPriority::Normal,
            "test_job".to_string(),
            EventPayload::File {
                file_id: "test_file".to_string(),
                filename: "test.txt".to_string(),
                file_size: 1000,
                bytes_copied: 0,
                destination_path: "/dest".to_string(),
                source_checksum: None,
                destination_checksum: None,
                hash_algorithm: "xxHash64BE".to_string(),
                transfer_speed_mbps: 0.0,
                error_message: None,
            },
        );

        hub.emit_event(file_event)
            .expect("Failed to emit file event");

        // Give time for event processing
        std::thread::sleep(Duration::from_millis(100));

        // Verify file handler received the event
        assert!(file_handler.events_received.load(Ordering::Relaxed) > 0);
        assert_eq!(dest_handler.events_received.load(Ordering::Relaxed), 0);

        let _ = hub.shutdown();
    }
}
