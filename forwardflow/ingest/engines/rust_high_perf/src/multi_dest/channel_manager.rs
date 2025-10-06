//! Monitored unbounded channels for independent-speed destinations

use crossbeam_channel::{unbounded, Sender, Receiver, SendError};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use super::types::WorkerCommand;

/// Sender that tracks memory usage for backpressure control
pub struct MonitoredSender {
    /// Underlying unbounded channel sender
    sender: Sender<WorkerCommand>,
    /// Atomic counter tracking bytes currently queued
    memory_tracker: Arc<AtomicUsize>,
    /// Chunk size for memory calculations
    chunk_size: usize,
}

impl MonitoredSender {
    /// Create new monitored sender
    pub fn new(
        sender: Sender<WorkerCommand>,
        memory_tracker: Arc<AtomicUsize>,
        chunk_size: usize,
    ) -> Self {
        Self {
            sender,
            memory_tracker,
            chunk_size,
        }
    }

    /// Send command and update memory tracking
    ///
    /// For Chunk commands, increments the memory counter by chunk size.
    /// This allows the memory monitor to track queue depth.
    pub fn send(&self, cmd: WorkerCommand) -> Result<(), SendError<WorkerCommand>> {
        // Track memory for chunk commands
        if let WorkerCommand::Chunk { ref data } = cmd {
            self.memory_tracker.fetch_add(data.len(), Ordering::Relaxed);
        }

        self.sender.send(cmd)
    }

    /// Decrease memory count (called by worker when chunk consumed)
    ///
    /// Workers call this after writing a chunk to disk to signal
    /// that memory has been freed for the queue.
    pub fn decrease_memory(&self, bytes: usize) {
        self.memory_tracker.fetch_sub(bytes, Ordering::Relaxed);
    }

    /// Get current queued memory in bytes
    pub fn queued_bytes(&self) -> usize {
        self.memory_tracker.load(Ordering::Relaxed)
    }

    /// Clone the sender for passing to worker
    ///
    /// The worker needs a clone to call decrease_memory after consuming chunks
    pub fn clone_sender(&self) -> Self {
        Self {
            sender: self.sender.clone(),
            memory_tracker: self.memory_tracker.clone(),
            chunk_size: self.chunk_size,
        }
    }
}

/// Create monitored unbounded channel pair
///
/// Returns (MonitoredSender, Receiver) where the sender tracks memory usage
pub fn create_monitored_channel(
    memory_tracker: Arc<AtomicUsize>,
    chunk_size: usize,
) -> (MonitoredSender, Receiver<WorkerCommand>) {
    let (tx, rx) = unbounded();
    let monitored_tx = MonitoredSender::new(tx, memory_tracker, chunk_size);
    (monitored_tx, rx)
}
