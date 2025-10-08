use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

/// Default maximum memory per destination queue (512 MB)
const DEFAULT_MAX_QUEUE_MEMORY_MB: usize = 512;

/// Sleep duration when applying backpressure (10ms)
const BACKPRESSURE_SLEEP_MS: u64 = 10;

/// Monitors memory usage across destination queues and applies backpressure
pub(crate) struct MemoryMonitor {
    /// Per-destination memory trackers (atomic counters of bytes in queue)
    queued_bytes: Vec<Arc<AtomicUsize>>,
    /// Maximum memory per destination in bytes
    max_per_dest_bytes: usize,
    /// Chunk size for calculations
    chunk_size: usize,
}

impl MemoryMonitor {
    /// Create a new memory monitor for the given number of destinations
    pub fn new(num_destinations: usize, chunk_size: usize) -> Self {
        let queued_bytes = (0..num_destinations)
            .map(|_| Arc::new(AtomicUsize::new(0)))
            .collect();

        Self {
            queued_bytes,
            max_per_dest_bytes: DEFAULT_MAX_QUEUE_MEMORY_MB * 1024 * 1024,
            chunk_size,
        }
    }

    /// Create with custom memory limit
    pub fn with_limit(num_destinations: usize, chunk_size: usize, max_mb_per_dest: usize) -> Self {
        let queued_bytes = (0..num_destinations)
            .map(|_| Arc::new(AtomicUsize::new(0)))
            .collect();

        Self {
            queued_bytes,
            max_per_dest_bytes: max_mb_per_dest * 1024 * 1024,
            chunk_size,
        }
    }

    /// Get memory tracker for a specific destination
    pub fn get_tracker(&self, dest_index: usize) -> Arc<AtomicUsize> {
        self.queued_bytes[dest_index].clone()
    }

    /// Check if we should apply backpressure (any destination over limit)
    pub fn should_backpressure(&self) -> bool {
        self.queued_bytes.iter().any(|bytes| {
            bytes.load(Ordering::Relaxed) > self.max_per_dest_bytes
        })
    }

    /// Apply backpressure by sleeping to let consumers catch up
    pub fn apply_backpressure(&self) {
        thread::sleep(Duration::from_millis(BACKPRESSURE_SLEEP_MS));
    }

    /// Get total memory usage across all destinations in MB
    pub fn total_memory_mb(&self) -> f64 {
        let total_bytes: usize = self.queued_bytes
            .iter()
            .map(|b| b.load(Ordering::Relaxed))
            .sum();
        total_bytes as f64 / (1024.0 * 1024.0)
    }

    /// Get memory usage for a specific destination in MB
    pub fn dest_memory_mb(&self, dest_index: usize) -> f64 {
        let bytes = self.queued_bytes[dest_index].load(Ordering::Relaxed);
        bytes as f64 / (1024.0 * 1024.0)
    }

    /// Get the slowest destination index (highest queue depth)
    pub fn slowest_destination(&self) -> Option<usize> {
        self.queued_bytes
            .iter()
            .enumerate()
            .max_by_key(|(_, bytes)| bytes.load(Ordering::Relaxed))
            .map(|(idx, _)| idx)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_monitor_creation() {
        let monitor = MemoryMonitor::new(3, 8 * 1024 * 1024);
        assert_eq!(monitor.total_memory_mb(), 0.0);
        assert!(!monitor.should_backpressure());
    }

    #[test]
    fn test_backpressure_threshold() {
        let monitor = MemoryMonitor::with_limit(2, 8 * 1024 * 1024, 10); // 10 MB limit
        
        // Add 5 MB to first destination - should not trigger backpressure
        let tracker = monitor.get_tracker(0);
        tracker.store(5 * 1024 * 1024, Ordering::Relaxed);
        assert!(!monitor.should_backpressure());
        
        // Add 15 MB to second destination - should trigger backpressure
        let tracker2 = monitor.get_tracker(1);
        tracker2.store(15 * 1024 * 1024, Ordering::Relaxed);
        assert!(monitor.should_backpressure());
    }

    #[test]
    fn test_slowest_destination() {
        let monitor = MemoryMonitor::new(3, 8 * 1024 * 1024);
        
        monitor.get_tracker(0).store(10 * 1024 * 1024, Ordering::Relaxed);
        monitor.get_tracker(1).store(50 * 1024 * 1024, Ordering::Relaxed);
        monitor.get_tracker(2).store(20 * 1024 * 1024, Ordering::Relaxed);
        
        assert_eq!(monitor.slowest_destination(), Some(1));
    }
}

