use anyhow::Result;
use crossbeam_channel::{unbounded, Receiver, Sender};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

use super::types::WorkerCommand;

/// A sender wrapper that tracks memory usage
pub(crate) struct MonitoredSender {
    sender: Sender<WorkerCommand>,
    memory_tracker: Arc<AtomicUsize>,
}

impl MonitoredSender {
    /// Create a new monitored sender
    pub fn new(sender: Sender<WorkerCommand>, memory_tracker: Arc<AtomicUsize>) -> Self {
        Self {
            sender,
            memory_tracker,
        }
    }

    /// Send a command and track memory if it's a chunk
    pub fn send(&self, cmd: WorkerCommand) -> Result<()> {
        // Track memory for Chunk commands
        if let WorkerCommand::Chunk { ref data } = cmd {
            self.memory_tracker.fetch_add(data.len(), Ordering::Relaxed);
        }

        self.sender
            .send(cmd)
            .map_err(|e| anyhow::anyhow!("Failed to send command: {}", e))
    }

    /// Decrease memory counter (called by worker after consuming chunk)
    pub fn decrease_memory(&self, bytes: usize) {
        self.memory_tracker.fetch_sub(bytes, Ordering::Relaxed);
    }

    /// Clone the memory tracker for worker use
    pub fn clone_tracker(&self) -> Arc<AtomicUsize> {
        Arc::clone(&self.memory_tracker)
    }
}

impl Clone for MonitoredSender {
    fn clone(&self) -> Self {
        Self {
            sender: self.sender.clone(),
            memory_tracker: Arc::clone(&self.memory_tracker),
        }
    }
}

/// Create a monitored unbounded channel
pub(crate) fn create_monitored_channel(
    memory_tracker: Arc<AtomicUsize>,
) -> (MonitoredSender, Receiver<WorkerCommand>) {
    let (tx, rx) = unbounded();
    let monitored_tx = MonitoredSender::new(tx, memory_tracker);
    (monitored_tx, rx)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    #[test]
    fn test_monitored_sender_tracks_memory() {
        let tracker = Arc::new(AtomicUsize::new(0));
        let (tx, _rx) = create_monitored_channel(Arc::clone(&tracker));

        // Send a chunk
        let data = Arc::new(vec![0u8; 1024]);
        tx.send(WorkerCommand::Chunk { data }).unwrap();

        // Should have tracked 1024 bytes
        assert_eq!(tracker.load(Ordering::Relaxed), 1024);

        // Decrease memory
        tx.decrease_memory(1024);
        assert_eq!(tracker.load(Ordering::Relaxed), 0);
    }
}

