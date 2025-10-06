# Multi-Destination Copy Refactoring Plan

## Current State
- `multi_dest_copy.rs`: **538 lines** (violates 300-line rule)
- Monolithic structure with memory monitoring needed

## New Architecture (All files < 300 lines)

```
src/multi_dest/
├── mod.rs                      (~50 lines)  - Public API & re-exports
├── engine.rs                   (~150 lines) - MultiDestCopyEngine (main orchestrator)
├── worker.rs                   (~180 lines) - DestinationWorker implementation
├── types.rs                    (~80 lines)  - Shared types & structs
├── memory_monitor.rs           (~120 lines) - Queue memory monitoring & backpressure
├── channel_manager.rs          (~100 lines) - Monitored channel creation & tracking
└── hasher.rs                   (~100 lines) - StreamingHasher implementation
```

## Module Breakdown

### 1. `src/multi_dest/mod.rs` (~50 lines)
**Purpose:** Public API and module organization
```rust
pub mod engine;
pub mod worker;
pub mod types;
pub mod memory_monitor;
pub mod channel_manager;
pub mod hasher;

// Re-export public API
pub use engine::MultiDestCopyEngine;
pub use types::{DestinationOutcome, MultiDestFileOutcome, ChunkProgress};
```

### 2. `src/multi_dest/types.rs` (~80 lines)
**Purpose:** All shared data structures
```rust
use std::path::PathBuf;
use std::sync::Arc;
use crate::verification::HashAlgorithm;

#[derive(Debug, Clone)]
pub struct DestinationOutcome { /* ... */ }

#[derive(Debug, Clone)]
pub struct MultiDestFileOutcome { /* ... */ }

pub struct ChunkProgress { /* ... */ }

pub(crate) enum WorkerCommand {
    StartFile { relative_path: PathBuf, hash_algorithm: HashAlgorithm },
    Chunk { data: Arc<Vec<u8>> },
    FinishFile,
}

pub(crate) struct WorkerResult { /* ... */ }
```

### 3. `src/multi_dest/memory_monitor.rs` (~120 lines)
**Purpose:** Memory monitoring and backpressure control
```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Duration;
use std::thread;

const DEFAULT_MAX_QUEUE_MEMORY_MB: usize = 512; // 512 MB per destination
const BACKPRESSURE_SLEEP_MS: u64 = 10;

pub struct MemoryMonitor {
    /// Total bytes currently queued across all destinations
    queued_bytes: Vec<Arc<AtomicUsize>>,
    /// Maximum memory per destination in bytes
    max_per_dest_bytes: usize,
    /// Chunk size for calculations
    chunk_size: usize,
}

impl MemoryMonitor {
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

    /// Apply backpressure by sleeping
    pub fn apply_backpressure(&self) {
        thread::sleep(Duration::from_millis(BACKPRESSURE_SLEEP_MS));
    }

    /// Get total memory usage across all destinations
    pub fn total_memory_mb(&self) -> f64 {
        let total_bytes: usize = self.queued_bytes.iter()
            .map(|b| b.load(Ordering::Relaxed))
            .sum();
        total_bytes as f64 / (1024.0 * 1024.0)
    }
}
```

### 4. `src/multi_dest/channel_manager.rs` (~100 lines)
**Purpose:** Create monitored unbounded channels
```rust
use crossbeam_channel::{unbounded, Sender, Receiver};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use super::types::WorkerCommand;

/// Monitored sender that tracks memory usage
pub struct MonitoredSender {
    sender: Sender<WorkerCommand>,
    memory_tracker: Arc<AtomicUsize>,
    chunk_size: usize,
}

impl MonitoredSender {
    pub fn new(
        sender: Sender<WorkerCommand>,
        memory_tracker: Arc<AtomicUsize>,
        chunk_size: usize,
    ) -> Self {
        Self { sender, memory_tracker, chunk_size }
    }

    /// Send command and update memory tracking
    pub fn send(&self, cmd: WorkerCommand) -> Result<(), crossbeam_channel::SendError<WorkerCommand>> {
        // Track memory for chunk commands
        if let WorkerCommand::Chunk { ref data } = cmd {
            self.memory_tracker.fetch_add(data.len(), Ordering::Relaxed);
        }

        self.sender.send(cmd)
    }

    /// Decrease memory count (called by worker when chunk consumed)
    pub fn decrease_memory(&self, bytes: usize) {
        self.memory_tracker.fetch_sub(bytes, Ordering::Relaxed);
    }
}

/// Create monitored channel pair
pub fn create_monitored_channel(
    memory_tracker: Arc<AtomicUsize>,
    chunk_size: usize,
) -> (MonitoredSender, Receiver<WorkerCommand>) {
    let (tx, rx) = unbounded();
    let monitored_tx = MonitoredSender::new(tx, memory_tracker, chunk_size);
    (monitored_tx, rx)
}
```

### 5. `src/multi_dest/hasher.rs` (~100 lines)
**Purpose:** Streaming hash calculation (extracted from multi_dest_copy.rs)
```rust
use crate::verification::HashAlgorithm;
use sha2::{Sha256, Digest as Sha2Digest};
use sha3::{Sha3_256, Digest as Sha3Digest};
// ... (existing StreamingHasher code)
```

### 6. `src/multi_dest/worker.rs` (~180 lines)
**Purpose:** DestinationWorker and ActiveFile (extracted from multi_dest_copy.rs)
```rust
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use crossbeam_channel::{Receiver, Sender};

use super::types::{WorkerCommand, WorkerResult};
use super::hasher::StreamingHasher;
use super::channel_manager::MonitoredSender;

pub(crate) struct DestinationWorker {
    dest_index: usize,
    dest_root: PathBuf,
    commands: Receiver<WorkerCommand>,
    results: Sender<WorkerResult>,
    cancelled: Arc<AtomicBool>,
    sender: Option<MonitoredSender>,  // NEW: For memory tracking
}

impl DestinationWorker {
    pub fn new(/* ... */, sender: MonitoredSender) -> Self {
        // Store sender for memory tracking
    }

    pub fn run(mut self) {
        // When consuming chunk, notify sender
        match command {
            WorkerCommand::Chunk { data } => {
                let chunk_size = data.len();
                // Write chunk...
                // IMPORTANT: Decrease memory counter after consuming
                if let Some(sender) = &self.sender {
                    sender.decrease_memory(chunk_size);
                }
            }
            // ...
        }
    }
}

struct ActiveFile { /* ... */ }
impl ActiveFile { /* ... */ }
```

### 7. `src/multi_dest/engine.rs` (~150 lines)
**Purpose:** Main MultiDestCopyEngine orchestrator
```rust
use std::sync::atomic::AtomicBool;
use std::sync::{Arc, Mutex};
use std::path::PathBuf;
use std::thread;
use crossbeam_channel::unbounded;

use crate::event_system::EventSystem;
use crate::verification::HashAlgorithm;

use super::types::*;
use super::worker::DestinationWorker;
use super::memory_monitor::MemoryMonitor;
use super::channel_manager::create_monitored_channel;
use super::hasher::StreamingHasher;

pub struct MultiDestCopyEngine {
    cancelled: Arc<AtomicBool>,
    chunk_size: usize,
}

impl MultiDestCopyEngine {
    pub fn copy<F>(/* ... */) -> Result<Vec<MultiDestFileOutcome>> {
        // Create memory monitor
        let memory_monitor = MemoryMonitor::new(dest_count, self.chunk_size);

        // Create monitored channels for each destination
        for (dest_index, dest_root) in destination_paths.iter().enumerate() {
            let memory_tracker = memory_monitor.get_tracker(dest_index);
            let (monitored_tx, rx) = create_monitored_channel(memory_tracker, self.chunk_size);

            let worker = DestinationWorker::new(
                dest_index,
                PathBuf::from(dest_root),
                rx,
                result_tx.clone(),
                Arc::clone(&self.cancelled),
                monitored_tx.clone(),  // Pass for memory tracking
            );

            worker_senders.push(monitored_tx);
            // ...
        }

        // Main copy loop with backpressure
        loop {
            let bytes_read = source_reader.read(&mut chunk_buffer)?;
            // ...

            // Send to all destinations (unbounded, non-blocking)
            for sender in &worker_senders {
                sender.send(WorkerCommand::Chunk { data: Arc::clone(&shared_chunk) })?;
            }

            // Apply backpressure if any destination queue is too large
            if memory_monitor.should_backpressure() {
                println!("⚠️  Backpressure: Memory usage {:.1} MB - slowing producer",
                    memory_monitor.total_memory_mb());
                memory_monitor.apply_backpressure();
            }
        }
    }
}
```

## Migration Steps

1. **Create directory structure:**
   ```bash
   mkdir -p src/multi_dest
   ```

2. **Create files in order:**
   - `types.rs` (no dependencies)
   - `hasher.rs` (depends on types)
   - `memory_monitor.rs` (standalone)
   - `channel_manager.rs` (depends on types, memory_monitor)
   - `worker.rs` (depends on types, hasher, channel_manager)
   - `engine.rs` (depends on all above)
   - `mod.rs` (re-exports)

3. **Update `lib.rs`:**
   ```rust
   pub mod multi_dest;  // Replace: pub mod multi_dest_copy;
   ```

4. **Update imports in `engine_core.rs`:**
   ```rust
   use crate::multi_dest::{MultiDestCopyEngine, DestinationOutcome, MultiDestFileOutcome};
   // Was: use crate::multi_dest_copy::{...};
   ```

## File Size Guarantees

| File | Lines | Status |
|------|-------|--------|
| `types.rs` | ~80 | ✅ < 300 |
| `hasher.rs` | ~100 | ✅ < 300 |
| `memory_monitor.rs` | ~120 | ✅ < 300 |
| `channel_manager.rs` | ~100 | ✅ < 300 |
| `worker.rs` | ~180 | ✅ < 300 |
| `engine.rs` | ~150 | ✅ < 300 |
| `mod.rs` | ~50 | ✅ < 300 |

**Total:** ~780 lines (was 538 + monitoring would be 650+)

## Benefits

1. ✅ **Clean separation of concerns**
2. ✅ **All files < 300 lines**
3. ✅ **Memory monitoring with backpressure**
4. ✅ **Unbounded channels for independent speeds**
5. ✅ **Proper module hierarchy**
6. ✅ **Easy to test each component**
7. ✅ **Easy to maintain and extend**
