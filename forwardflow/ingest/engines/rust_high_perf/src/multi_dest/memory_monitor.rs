//! Memory monitoring and backpressure control for multi-destination copy

use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Duration;
use std::thread;

/// Default maximum memory per destination queue (512 MB)
const DEFAULT_MAX_QUEUE_MEMORY_MB: usize = 512;

/// Sleep duration when applying backpressure (10ms)
const BACKPRESSURE_SLEEP_MS: u64 = 10;

/// Monitors memory usage across destination queues and applies backpressure
pub struct MemoryMonitor {
    /// Atomic counters for bytes queued per destination
    queued_bytes: Vec<Arc<AtomicUsize>>,
    /// Maximum memory allowed per destination in bytes
    max_per_dest_bytes: usize,
    /// Chunk size for memory calculations
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

    /// Create monitor with custom memory limit per destination
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

    /// Apply backpressure by sleeping to allow consumers to catch up
    pub fn apply_backpressure(&self) {
        thread::sleep(Duration::from_millis(BACKPRESSURE_SLEEP_MS));
    }

    /// Get total memory usage across all destinations in MB
    pub fn total_memory_mb(&self) -> f64 {
        let total_bytes: usize = self.queued_bytes.iter()
            .map(|b| b.load(Ordering::Relaxed))
            .sum();
        total_bytes as f64 / (1024.0 * 1024.0)
    }

    /// Get memory usage for a specific destination in MB
    pub fn dest_memory_mb(&self, dest_index: usize) -> f64 {
        let bytes = self.queued_bytes[dest_index].load(Ordering::Relaxed);
        bytes as f64 / (1024.0 * 1024.0)
    }

    /// Get percentage of memory limit used for a destination
    pub fn dest_usage_percent(&self, dest_index: usize) -> f64 {
        let bytes = self.queued_bytes[dest_index].load(Ordering::Relaxed);
        (bytes as f64 / self.max_per_dest_bytes as f64) * 100.0
    }

    /// Check if a specific destination is over limit
    pub fn is_dest_over_limit(&self, dest_index: usize) -> bool {
        self.queued_bytes[dest_index].load(Ordering::Relaxed) > self.max_per_dest_bytes
    }

    /// Get statistics for all destinations
    pub fn get_stats(&self) -> MemoryStats {
        let per_dest: Vec<f64> = (0..self.queued_bytes.len())
            .map(|i| self.dest_memory_mb(i))
            .collect();

        let total = self.total_memory_mb();
        let max_dest = per_dest.iter().cloned().fold(0.0f64, f64::max);
        let over_limit = self.should_backpressure();

        MemoryStats {
            total_mb: total,
            max_dest_mb: max_dest,
            per_dest_mb: per_dest,
            over_limit,
        }
    }
}

/// Memory usage statistics
#[derive(Debug, Clone)]
pub struct MemoryStats {
    /// Total memory across all destinations (MB)
    pub total_mb: f64,
    /// Maximum memory for any single destination (MB)
    pub max_dest_mb: f64,
    /// Memory per destination (MB)
    pub per_dest_mb: Vec<f64>,
    /// Whether any destination is over limit
    pub over_limit: bool,
}
