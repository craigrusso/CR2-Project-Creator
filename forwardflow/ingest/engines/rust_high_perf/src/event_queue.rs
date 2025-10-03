//! Lock-free event queue for Rust → Python communication
//!
//! This module provides a thread-safe, GIL-free event queue using crossbeam channels.
//! Events are sent from Rust file copy threads WITHOUT acquiring Python's GIL,
//! and consumed by a Python event pump thread that polls the queue periodically.

use crossbeam::channel::{bounded, Receiver, Sender, TryRecvError};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

/// Event types that can be sent from Rust to Python
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TransferEvent {
    /// Job started
    JobStarted {
        job_id: String,
        total_files: usize,
        total_bytes: u64,
        destinations: Vec<String>,
    },

    /// Job progress update
    JobProgress {
        job_id: String,
        bytes_copied: u64,
        total_bytes: u64,
        files_completed: usize,
        total_files: usize,
        elapsed_s: f64,
        speed_mbps: f64,
        current_speed_mbps: f64,
        peak_speed_mbps: f64,
    },

    /// File transfer started
    FileStarted {
        file_id: String,
        filename: String,
        source_path: String,
        dest_path: String,
        total_bytes: u64,
    },

    /// File progress update
    FileProgress {
        filename: String,
        bytes_copied: u64,
        total_bytes: u64,
        speed_mbps: f64,
    },

    /// File transfer completed
    FileCompleted {
        filename: String,
        source_path: String,
        dest_path: String,
        dest_index: usize,
        bytes_copied: u64,
        source_checksum: String,
        dest_checksum: String,
        hash_algorithm: String,
        verification_passed: bool,
        status: String,
    },

    /// Destination progress update
    DestProgress {
        dest_index: usize,
        dest_path: String,
        transfer_type: String,
        bytes_copied: u64,
        total_bytes: u64,
        current_speed_mbps: f64,
        peak_speed_mbps: f64,
        elapsed_time: f64,
        completed_files: usize,
        total_files: usize,
        progress_percent: f64,
    },

    /// Destination completed
    DestCompleted {
        dest_index: usize,
        dest_path: String,
        bytes_copied: u64,
        total_bytes: u64,
        completed_files: usize,
        total_files: usize,
        elapsed_time: f64,
    },

    /// Error event
    Error {
        message: String,
        context: Option<String>,
    },
}

/// Lock-free event queue for Rust → Python communication
pub struct EventQueue {
    sender: Sender<TransferEvent>,
    receiver: Arc<Receiver<TransferEvent>>,
}

impl EventQueue {
    /// Create a new event queue with specified capacity
    ///
    /// Capacity of 10,000 events is more than enough for real-time updates
    pub fn new(capacity: usize) -> Self {
        let (sender, receiver) = bounded(capacity);
        Self {
            sender,
            receiver: Arc::new(receiver),
        }
    }

    /// Create event queue with default capacity (10,000 events)
    pub fn with_default_capacity() -> Self {
        Self::new(10_000)
    }

    /// Send an event to the queue (non-blocking, no GIL needed)
    ///
    /// Returns Ok(()) if event was sent, Err if queue is full
    pub fn send(&self, event: TransferEvent) -> Result<(), String> {
        self.sender
            .try_send(event)
            .map_err(|e| format!("Event queue full: {}", e))
    }

    /// Try to receive a single event (non-blocking)
    ///
    /// Returns Some(event) if event available, None if queue is empty
    pub fn try_recv(&self) -> Option<TransferEvent> {
        match self.receiver.try_recv() {
            Ok(event) => Some(event),
            Err(TryRecvError::Empty) => None,
            Err(TryRecvError::Disconnected) => None,
        }
    }

    /// Drain all pending events from queue (non-blocking)
    ///
    /// Returns a vector of all currently queued events
    pub fn drain_all(&self) -> Vec<TransferEvent> {
        let mut events = Vec::new();
        while let Some(event) = self.try_recv() {
            events.push(event);
        }
        events
    }

    /// Get approximate number of events in queue
    pub fn len(&self) -> usize {
        self.receiver.len()
    }

    /// Check if queue is empty
    pub fn is_empty(&self) -> bool {
        self.receiver.is_empty()
    }

    /// Clone the sender for use in other threads
    pub fn clone_sender(&self) -> Sender<TransferEvent> {
        self.sender.clone()
    }

    /// Get a reference to the receiver (for sharing across threads)
    pub fn get_receiver(&self) -> Arc<Receiver<TransferEvent>> {
        Arc::clone(&self.receiver)
    }
}

impl Clone for EventQueue {
    fn clone(&self) -> Self {
        Self {
            sender: self.sender.clone(),
            receiver: Arc::clone(&self.receiver),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_event_queue_send_recv() {
        let queue = EventQueue::new(100);

        let event = TransferEvent::JobStarted {
            job_id: "test_job".to_string(),
            total_files: 10,
            total_bytes: 1000,
            destinations: vec!["dest1".to_string()],
        };

        assert!(queue.send(event.clone()).is_ok());
        assert_eq!(queue.len(), 1);

        let received = queue.try_recv();
        assert!(received.is_some());
        assert!(queue.is_empty());
    }

    #[test]
    fn test_event_queue_drain() {
        let queue = EventQueue::with_default_capacity();

        for i in 0..5 {
            let event = TransferEvent::JobProgress {
                job_id: format!("job_{}", i),
                bytes_copied: 100,
                total_bytes: 1000,
                files_completed: 1,
                total_files: 10,
                elapsed_s: 1.0,
                speed_mbps: 100.0,
                current_speed_mbps: 100.0,
                peak_speed_mbps: 100.0,
            };
            queue.send(event).unwrap();
        }

        assert_eq!(queue.len(), 5);
        let events = queue.drain_all();
        assert_eq!(events.len(), 5);
        assert!(queue.is_empty());
    }
}
